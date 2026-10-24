"""Copy the user's existing APKs without changing, signing or publishing them."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

# These are user-facing translations, not claims of official Sony product names.
TRANSLATIONS = {
    '01': ('延时摄影扩展', '延时摄影的附加组件，不建议单独作为第一个安装测试。', '名称由原清单的资源字符串推断；具体功能和依赖需真机确认。'),
    '02': ('延时摄影', '按设定的间隔拍摄连续照片，用于记录云朵、日落等缓慢变化。', ''),
    '03': ('平滑反射', '通过多张照片合成，营造平滑水面或柔和反射的效果。', ''),
    '04': ('实时色彩预设（名称待确认）', '原清单将它识别为 Live View Grading 预设应用，便于尝试不同色彩风格。', '名称及用途来自资源字符串推断，不是已核实的官方中文名称。'),
    '05': ('光绘', '用于尝试光轨、灯光绘画等创意拍摄。', ''),
    '06': ('专业包围拍摄', '原清单发现了对焦、光圈及闪光包围拍摄的相关资源，可尝试比较不同拍摄参数。', '具体支持的包围模式受相机和镜头限制。'),
    '07': ('人像美化', '提供人像美化相关效果，方便尝试不同的人像风格。', ''),
    '08': ('定格动画', '逐张拍摄静态场景，用连续画面制作定格动画。', ''),
    '09': ('照片润饰', '在相机上进行简单的照片编辑和润饰。', ''),
    '10': ('渐变滤镜', '用于调整画面不同区域的效果，例如天空与地面的明暗。', ''),
    '11': ('手动镜头补偿', '用于手动镜头相关的补偿设置；具体参数请以应用内说明为准。', ''),
    '12': ('增强图片效果', '提供额外图片效果，便于尝试创意成像。', ''),
    '13': ('非接触快门', '用于尝试非接触式快门触发；触发方式请以应用内说明为准。', ''),
    '14': ('光线效果', '用于尝试光束、眩光等光线表现效果。', '名称及用途由原清单的 ANGELLADDER、BEAM、FLARE 资源字符串推断。'),
    '15': ('多重曝光', '将多次曝光叠加，创作合成画面。', ''),
    '16': ('智能遥控', '配合兼容的手机应用进行遥控拍摄。', '手机端兼容性和可用功能需要另行验证，不保证所有现代手机应用都能连接。'),
    '17': ('运动轨迹', '将连续运动中的不同位置合成到一张画面中。', ''),
    '18': ('星轨', '用于拍摄并合成星星随时间移动形成的轨迹。', ''),
    '19': ('数码滤镜', '用于对画面区域进行滤镜调整，例如分别处理天空和地面。', ''),
    '20': ('人像光效', '提供人像光照相关的效果调整。', ''),
    '21': ('影像配方实验室（Recipe Lab）', '社区应用；具体功能请以 Recipe Lab 自身说明为准。', '本列表提供中文说明，不会改变 Recipe Lab 在相机内的界面语言。'),
}


def import_apps(source, destination):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    manifest = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    if len(manifest) != 21 or {item['id'] for item in manifest} != set(TRANSLATIONS):
        raise ValueError('Expected the original manifest with exactly 21 unique app IDs')
    entries = []
    # Validate the entire source first, so a bad manifest does not create a partial catalog.
    for item in manifest:
        filename = item['file']
        if Path(filename).name != filename or '/' in filename or '\\' in filename:
            raise ValueError('Invalid APK filename: ' + filename)
        path = (source / filename).resolve()
        if path.parent != source:
            raise ValueError('APK is outside source directory')
        data = path.read_bytes()
        if not data.startswith(b'PK') or not 0 < len(data) <= 64 * 1024 ** 2:
            raise ValueError('Invalid APK size or ZIP header: ' + filename)
        name, description, note = TRANSLATIONS[item['id']]
        entries.append({
            'id': item['id'], 'name': item['name'], 'nameZh': name,
            'descriptionZh': description, 'noteZh': note,
            'package': item['package'], 'versionName': item['versionName'],
            'file': filename, 'locales': item['locales'],
            'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
        })
    destination.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        target = destination / entry['file']
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Refusing to overwrite a different APK: ' + str(target))
        shutil.copyfile(source / entry['file'], target)
        if hashlib.sha256(target.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('APK changed during copy: ' + entry['file'])
    catalog = {'version': 1, 'source': 'User-provided private APK collection; redistribution not authorized by this project.',
               'apps': sorted(entries, key=lambda entry: entry['id'])}
    (destination / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return entries


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', help='Original payload/apps directory containing manifest.json')
    parser.add_argument('--output', default=str(Path(__file__).resolve().parents[1] / 'offline-apps'))
    args = parser.parse_args()
    entries = import_apps(args.source, args.output)
    print('Copied and SHA-256 verified %d unchanged APKs to %s' % (len(entries), args.output))
