"""Exercise the real local TLS/HTTP/SPK path with synthetic peers, not a camera.

All TCP connections stay on loopback. This verifies frozen runtime behavior,
not camera certificate acceptance, device compatibility or installation success.
"""
import http.client
import json
import socket

import tlslite
from tlslite.utils import python_aes

from .server import LocalMarketServer, ServerContext, TLSConnection
from .. import spk


def verify_python_aes():
    """NIST SP 800-38A CBC vectors, including the source-inspecting TLS backend."""
    plaintext = bytes.fromhex('6bc1bee22e409f96e93d7e117393172a')
    iv = bytes.fromhex('000102030405060708090a0b0c0d0e0f')
    vectors = [
        ('2b7e151628aed2a6abf7158809cf4f3c', '7649abac8119b246cee98e9b12e9197d'),
        ('603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4',
         'f58c4c04d6e5f1ba779eabfb5f7bfbd6'),
    ]
    for key_hex, ciphertext_hex in vectors:
        key, ciphertext = bytes.fromhex(key_hex), bytes.fromhex(ciphertext_hex)
        encryptor = python_aes.new(key, 2, iv)
        decryptor = python_aes.new(key, 2, iv)
        if bytes(encryptor.encrypt(plaintext)) != ciphertext:
            raise RuntimeError('TLS Python AES-CBC encryption self-test failed')
        if bytes(decryptor.decrypt(bytearray(ciphertext))) != plaintext:
            raise RuntimeError('TLS Python AES-CBC decryption self-test failed')
    return True


def _request(server, version, method, body=b''):
    settings = tlslite.HandshakeSettings()
    settings.minVersion = settings.maxVersion = version
    settings.cipherNames = ['aes128']
    settings.macNames = ['sha']
    settings.keyExchangeNames = ['rsa']
    settings.cipherImplementations = ['python']
    # These settings restrict only this synthetic client. The installation
    # server keeps its normal upstream settings and original certificate.
    connection = TLSConnection(socket.create_connection(server.server_address, timeout=10))
    response = None
    try:
        connection.handshakeClientCert(settings=settings)
        request = ('%s / HTTP/1.0\r\nHost: 127.0.0.1\r\nContent-Length: %d\r\n\r\n'
                   % (method, len(body))).encode('ascii') + body
        connection.sendall(request)
        response = http.client.HTTPResponse(connection)
        response.begin()
        # HTTPResponse.read handles partial TLS/socket reads and Content-Length.
        data = response.read()
        if response.status != 200 or connection.version != version:
            raise RuntimeError('Unexpected local TLS/HTTP self-test response')
        return data, connection.getCipherName()
    finally:
        if response is not None:
            response.close()
        connection.close()


def verify_local_tls(cert_file):
    """Use the real market server on an ephemeral loopback port; no USB calls."""
    verify_python_aes()
    reports = []
    for version, name in [((3, 1), 'TLS 1.0'), ((3, 3), 'TLS 1.2')]:
        apk = b'PK\x03\x04 synthetic self-test APK bytes ' + name.encode('ascii')
        with ServerContext(LocalMarketServer(str(cert_file), port=0)) as server:
            if server.server_address[0] != '127.0.0.1':
                raise RuntimeError('TLS self-test must stay on loopback')
            server.setApk(apk)
            request_body = b'{"selftest":true}'
            data, cipher = _request(server, version, 'POST', request_body)
            action = json.loads(data)['actions'][0]
            if action['command'] != 'dlandinstall' or action['args'] != server.url:
                raise RuntimeError('Local market action self-test failed')
            data, _ = _request(server, version, 'GET')
            if spk.parse(data) != apk:
                raise RuntimeError('TLS/HTTP/SPK payload self-test failed')
            data, _ = _request(server, version, 'POST', request_body)
            if json.loads(data)['actions'] != [] or server.getResult() != {'selftest': True}:
                raise RuntimeError('Local market completion self-test failed')
            reports.append({'version': name, 'cipher': cipher, 'httpVerified': True,
                            'spkRoundTripVerified': True, 'cameraConnected': False})
    return reports
