package main

import (
	"bytes"
	"crypto/sha256"
	"embed"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"mime"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"sync"
	"time"
)

//go:embed payload/**
var payload embed.FS

type appItem struct {
	ID          string   `json:"id"`
	Name        string   `json:"name"`
	File        string   `json:"file"`
	DownloadURL string   `json:"downloadUrl,omitempty"`
	Note        string   `json:"note"`
	Package     string   `json:"package,omitempty"`
	VersionName string   `json:"versionName,omitempty"`
	Locales     []string `json:"locales,omitempty"`
	Chinese     bool     `json:"chinese"`
	ChineseNote string   `json:"chineseNote,omitempty"`
	SHA256      string   `json:"sha256,omitempty"`
	Size        int64    `json:"size,omitempty"`
	Source      string   `json:"source,omitempty"`
}

type installRequest struct {
	ID     string `json:"id"`
	Driver string `json:"driver"`
}

type catalogRequest struct {
	URL string `json:"url"`
}

type remoteCatalog struct {
	Version int       `json:"version"`
	Apps    []appItem `json:"apps"`
}

type appConfig struct {
	CatalogURL string `json:"catalogUrl"`
}

const defaultCatalogURL = "https://raw.githubusercontent.com/kkkhs/a6000-clean-installer/main/catalog/a6000-catalog.json"

type statusState struct {
	Running bool     `json:"running"`
	Message string   `json:"message"`
	Log     []string `json:"log"`
	WorkDir string   `json:"workDir"`
}

var (
	embeddedApps []appItem
	apps         []appItem
	workDir      string
	catalogMu    sync.RWMutex
	statusMu     sync.Mutex
	status       statusState
	installMu    sync.Mutex
)

var pythonDependencies = []struct {
	Module  string
	Package string
}{
	{"certifi", "certifi"},
	{"comtypes", "comtypes"},
	{"Crypto", "pycryptodome"},
	{"usb", "pyusb"},
	{"yaml", "pyyaml"},
}

func main() {
	var err error
	workDir, err = prepareWorkspace()
	if err != nil {
		log.Fatal(err)
	}
	status.WorkDir = workDir
	apps, err = loadApps()
	if err != nil {
		log.Fatal(err)
	}
	if err := enrichApps(); err != nil {
		log.Fatal(err)
	}
	embeddedApps = append([]appItem(nil), apps...)
	loadConfiguredCatalog()

	mux := http.NewServeMux()
	mux.HandleFunc("/", handleIndex)
	mux.HandleFunc("/api/apps", handleApps)
	mux.HandleFunc("/api/install", handleInstall)
	mux.HandleFunc("/api/catalog", handleCatalog)
	mux.HandleFunc("/api/status", handleStatus)

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	url := "http://" + ln.Addr().String()
	fmt.Println("A6000 Clean Installer")
	fmt.Println("UI:", url)
	fmt.Println("Workspace:", workDir)
	openBrowser(url)
	log.Fatal(http.Serve(ln, mux))
}

func loadConfiguredCatalog() {
	cfg, ok := readConfig()
	catalogURL := defaultCatalogURL
	if ok && cfg.CatalogURL != "" {
		catalogURL = cfg.CatalogURL
	}
	if catalogURL == "" {
		return
	}
	remote, err := loadRemoteCatalog(catalogURL)
	if err != nil {
		appendLog("Remote catalog failed: " + err.Error())
		return
	}
	catalogMu.Lock()
	apps = append(append([]appItem(nil), embeddedApps...), remote...)
	catalogMu.Unlock()
	appendLog(fmt.Sprintf("Loaded remote catalog: %d apps", len(remote)))
}

func readConfig() (appConfig, bool) {
	var cfg appConfig
	paths := []string{}
	if exe, err := os.Executable(); err == nil {
		paths = append(paths, filepath.Join(filepath.Dir(exe), "A6000CleanInstaller.config.json"))
	}
	paths = append(paths, filepath.Join(workDir, "A6000CleanInstaller.config.json"))
	for _, path := range paths {
		b, err := os.ReadFile(path)
		if err != nil {
			continue
		}
		if err := json.Unmarshal(b, &cfg); err != nil {
			appendLog("Config parse failed: " + err.Error())
			return appConfig{}, false
		}
		return cfg, true
	}
	return appConfig{}, false
}

func prepareWorkspace() (string, error) {
	base, err := os.UserCacheDir()
	if err != nil {
		base = os.TempDir()
	}
	dir := filepath.Join(base, "A6000CleanInstaller")
	if err := os.RemoveAll(dir); err != nil {
		return "", err
	}
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", err
	}
	return dir, copyPayload("payload", dir)
}

func copyPayload(src, dst string) error {
	entries, err := payload.ReadDir(src)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		from := src + "/" + entry.Name()
		to := filepath.Join(dst, entry.Name())
		if entry.IsDir() {
			if err := os.MkdirAll(to, 0755); err != nil {
				return err
			}
			if err := copyPayload(from, to); err != nil {
				return err
			}
			continue
		}
		b, err := payload.ReadFile(from)
		if err != nil {
			return err
		}
		if err := os.WriteFile(to, b, 0644); err != nil {
			return err
		}
	}
	return nil
}

func loadApps() ([]appItem, error) {
	b, err := payload.ReadFile("payload/apps/manifest.json")
	if err != nil {
		return nil, err
	}
	var items []appItem
	if err := json.Unmarshal(b, &items); err != nil {
		return nil, err
	}
	sort.Slice(items, func(i, j int) bool { return items[i].ID < items[j].ID })
	return items, nil
}

func enrichApps() error {
	for i := range apps {
		apps[i].Source = "embedded"
		path := filepath.Join(workDir, "apps", apps[i].File)
		f, err := os.Open(path)
		if err != nil {
			return err
		}
		h := sha256.New()
		n, err := io.Copy(h, f)
		closeErr := f.Close()
		if err != nil {
			return err
		}
		if closeErr != nil {
			return closeErr
		}
		apps[i].SHA256 = hex.EncodeToString(h.Sum(nil))
		apps[i].Size = n
	}
	return nil
}

func handleIndex(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	_, _ = io.WriteString(w, indexHTML)
}

func handleApps(w http.ResponseWriter, r *http.Request) {
	catalogMu.RLock()
	defer catalogMu.RUnlock()
	writeJSON(w, apps)
}

func handleStatus(w http.ResponseWriter, r *http.Request) {
	statusMu.Lock()
	defer statusMu.Unlock()
	writeJSON(w, status)
}

func handleInstall(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	var req installRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	item, ok := findApp(req.ID)
	if !ok {
		http.Error(w, "unknown app id", http.StatusBadRequest)
		return
	}
	if req.Driver != "" && req.Driver != "native" && req.Driver != "libusb" {
		http.Error(w, "driver must be native, libusb, or empty", http.StatusBadRequest)
		return
	}
	if !installMu.TryLock() {
		http.Error(w, "another install is running", http.StatusConflict)
		return
	}
	setStatus(true, "Installing "+item.Name, nil)
	go func() {
		defer installMu.Unlock()
		err := runInstall(item, req.Driver)
		if err != nil {
			appendLog("ERROR: " + err.Error())
			setRunning(false, "Failed")
			return
		}
		setRunning(false, "Done")
	}()
	writeJSON(w, map[string]string{"status": "started"})
}

func handleCatalog(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	var req catalogRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	remote, err := loadRemoteCatalog(req.URL)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	catalogMu.Lock()
	apps = append(append([]appItem(nil), embeddedApps...), remote...)
	catalogMu.Unlock()
	writeJSON(w, map[string]any{"status": "loaded", "remoteApps": len(remote), "totalApps": len(apps)})
}

func runInstall(item appItem, driver string) error {
	python, args, err := findPython()
	if err != nil {
		return err
	}
	if err := ensurePythonDependencies(python, args); err != nil {
		return err
	}
	apk, err := resolveAPK(item)
	if err != nil {
		return err
	}
	pmcaDir := filepath.Join(workDir, "pmca")
	cmdArgs := append(args, "pmca-console.py", "install")
	if driver != "" {
		cmdArgs = append(cmdArgs, "-d", driver)
	}
	cmdArgs = append(cmdArgs, "-f", apk)
	appendLog("Command: " + python + " " + strings.Join(cmdArgs, " "))
	appendLog("Tip: connect the camera by USB and put it in the required install mode.")
	cmd := exec.Command(python, cmdArgs...)
	cmd.Dir = pmcaDir
	cmd.Env = append(os.Environ(), "PYTHONIOENCODING=utf-8")
	out, err := cmd.CombinedOutput()
	for _, line := range strings.Split(strings.ReplaceAll(string(out), "\r\n", "\n"), "\n") {
		if strings.TrimSpace(line) != "" {
			appendLog(line)
		}
	}
	if err != nil {
		appendLog("If Python dependencies are missing, run:")
		appendLog(pythonCommand(python, args, "-m", "pip", "install", "--user", "--upgrade", "certifi", "comtypes", "pycryptodome", "pyusb", "pyyaml"))
		return err
	}
	return nil
}

func ensurePythonDependencies(python string, args []string) error {
	missing, err := missingPythonDependencies(python, args)
	if err != nil {
		return err
	}
	if len(missing) == 0 {
		appendLog("Python dependencies: OK")
		return nil
	}
	packages := missingPackages(missing)
	appendLog("Missing Python modules: " + strings.Join(missing, ", "))
	appendLog("Installing Python packages: " + strings.Join(packages, ", "))
	if err := ensurePip(python, args); err != nil {
		return err
	}
	if err := runPythonLogged(python, args, append([]string{"-m", "pip", "install", "--user", "--upgrade"}, packages...)...); err != nil {
		return err
	}
	missing, err = missingPythonDependencies(python, args)
	if err != nil {
		return err
	}
	if len(missing) > 0 {
		return fmt.Errorf("python dependency install finished, but still missing: %s", strings.Join(missing, ", "))
	}
	appendLog("Python dependencies installed.")
	return nil
}

func missingPythonDependencies(python string, args []string) ([]string, error) {
	modules := make([]string, 0, len(pythonDependencies))
	for _, dep := range pythonDependencies {
		modules = append(modules, dep.Module)
	}
	code := "import importlib.util, json\nmods=" + pythonListLiteral(modules) + "\nprint(json.dumps([m for m in mods if importlib.util.find_spec(m) is None]))\n"
	out, err := runPython(python, args, "-c", code)
	if err != nil {
		return nil, fmt.Errorf("python dependency check failed: %w", err)
	}
	var missing []string
	if err := json.Unmarshal(bytes.TrimSpace(out), &missing); err != nil {
		return nil, fmt.Errorf("python dependency check parse failed: %w", err)
	}
	return missing, nil
}

func missingPackages(missing []string) []string {
	seen := map[string]bool{}
	var packages []string
	for _, module := range missing {
		for _, dep := range pythonDependencies {
			if dep.Module == module && !seen[dep.Package] {
				seen[dep.Package] = true
				packages = append(packages, dep.Package)
			}
		}
	}
	return packages
}

func ensurePip(python string, args []string) error {
	if _, err := runPython(python, args, "-m", "pip", "--version"); err == nil {
		return nil
	}
	appendLog("pip was not found. Trying ensurepip...")
	if err := runPythonLogged(python, args, "-m", "ensurepip", "--upgrade"); err != nil {
		return fmt.Errorf("pip is not available and ensurepip failed: %w", err)
	}
	return nil
}

func runPythonLogged(python string, args []string, extra ...string) error {
	appendLog("Command: " + pythonCommand(python, args, extra...))
	out, err := runPython(python, args, extra...)
	for _, line := range strings.Split(strings.ReplaceAll(string(out), "\r\n", "\n"), "\n") {
		if strings.TrimSpace(line) != "" {
			appendLog(line)
		}
	}
	return err
}

func runPython(python string, args []string, extra ...string) ([]byte, error) {
	cmdArgs := append(append([]string{}, args...), extra...)
	cmd := exec.Command(python, cmdArgs...)
	cmd.Env = append(os.Environ(), "PYTHONIOENCODING=utf-8")
	return cmd.CombinedOutput()
}

func pythonCommand(python string, args []string, extra ...string) string {
	all := append(append([]string{python}, args...), extra...)
	return strings.Join(all, " ")
}

func pythonListLiteral(items []string) string {
	b, _ := json.Marshal(items)
	return string(b)
}

func resolveAPK(item appItem) (string, error) {
	if item.DownloadURL == "" {
		return filepath.Join(workDir, "apps", item.File), nil
	}
	if item.SHA256 == "" {
		return "", errors.New("remote app is missing sha256")
	}
	dir := filepath.Join(workDir, "downloads")
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", err
	}
	name := safeName(item.ID+"-"+item.Name) + ".apk"
	path := filepath.Join(dir, name)
	if ok, _ := fileSHA256Matches(path, item.SHA256); ok {
		appendLog("Using cached APK: " + path)
		return path, nil
	}
	appendLog("Downloading: " + item.DownloadURL)
	req, err := http.NewRequest(http.MethodGet, item.DownloadURL, nil)
	if err != nil {
		return "", err
	}
	client := &http.Client{Timeout: 10 * time.Minute}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return "", fmt.Errorf("download failed: HTTP %d", resp.StatusCode)
	}
	tmp := path + ".tmp"
	f, err := os.Create(tmp)
	if err != nil {
		return "", err
	}
	h := sha256.New()
	n, copyErr := io.Copy(io.MultiWriter(f, h), resp.Body)
	closeErr := f.Close()
	if copyErr != nil {
		_ = os.Remove(tmp)
		return "", copyErr
	}
	if closeErr != nil {
		_ = os.Remove(tmp)
		return "", closeErr
	}
	sum := hex.EncodeToString(h.Sum(nil))
	if !strings.EqualFold(sum, item.SHA256) {
		_ = os.Remove(tmp)
		return "", fmt.Errorf("sha256 mismatch: got %s, want %s", sum, item.SHA256)
	}
	if item.Size > 0 && item.Size != n {
		appendLog(fmt.Sprintf("Downloaded size differs from catalog: got %d, catalog %d", n, item.Size))
	}
	if err := os.Rename(tmp, path); err != nil {
		return "", err
	}
	appendLog("Downloaded and verified: " + path)
	return path, nil
}

func loadRemoteCatalog(rawURL string) ([]appItem, error) {
	if rawURL == "" {
		return nil, errors.New("catalog url is required")
	}
	if !isAllowedRemoteURL(rawURL) {
		return nil, errors.New("catalog url must be https, localhost, or 127.0.0.1")
	}
	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Get(rawURL)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("catalog download failed: HTTP %d", resp.StatusCode)
	}
	body, err := io.ReadAll(io.LimitReader(resp.Body, 2<<20))
	if err != nil {
		return nil, err
	}
	var catalog remoteCatalog
	if err := json.Unmarshal(body, &catalog); err != nil {
		return nil, err
	}
	if catalog.Version != 1 {
		return nil, errors.New("catalog version must be 1")
	}
	seen := map[string]bool{}
	for i := range catalog.Apps {
		app := &catalog.Apps[i]
		if app.ID == "" || app.Name == "" || app.DownloadURL == "" || app.SHA256 == "" {
			return nil, errors.New("each remote app needs id, name, downloadUrl, and sha256")
		}
		if !isAllowedRemoteURL(app.DownloadURL) {
			return nil, errors.New("downloadUrl must be https, localhost, or 127.0.0.1 for app " + app.ID)
		}
		if !isHexSHA256(app.SHA256) {
			return nil, errors.New("bad sha256 for app " + app.ID)
		}
		if seen[app.ID] {
			return nil, errors.New("duplicate remote app id " + app.ID)
		}
		seen[app.ID] = true
		if findEmbeddedApp(app.ID) {
			app.ID = "remote-" + app.ID
		}
		app.File = ""
		app.Source = "remote"
	}
	return catalog.Apps, nil
}

func isAllowedRemoteURL(s string) bool {
	return strings.HasPrefix(s, "https://") || strings.HasPrefix(s, "http://127.0.0.1") || strings.HasPrefix(s, "http://localhost")
}

func fileSHA256Matches(path, want string) (bool, error) {
	f, err := os.Open(path)
	if err != nil {
		return false, err
	}
	defer f.Close()
	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return false, err
	}
	return strings.EqualFold(hex.EncodeToString(h.Sum(nil)), want), nil
}

func findPython() (string, []string, error) {
	if p := os.Getenv("A6000_PYTHON"); p != "" {
		return p, nil, nil
	}
	candidates := [][]string{{"py", "-3"}, {"python", ""}, {"python3", ""}}
	for _, c := range candidates {
		p, err := exec.LookPath(c[0])
		if err != nil {
			continue
		}
		var args []string
		if c[1] != "" {
			args = append(args, c[1])
		}
		return p, args, nil
	}
	return "", nil, errors.New("Python was not found. Install Python 3, then rerun this installer; PMCA modules will be installed automatically")
}

func findApp(id string) (appItem, bool) {
	catalogMu.RLock()
	defer catalogMu.RUnlock()
	for _, item := range apps {
		if item.ID == id {
			return item, true
		}
	}
	return appItem{}, false
}

func findEmbeddedApp(id string) bool {
	for _, item := range embeddedApps {
		if item.ID == id {
			return true
		}
	}
	return false
}

func isHexSHA256(s string) bool {
	if len(s) != 64 {
		return false
	}
	for _, r := range s {
		if !((r >= '0' && r <= '9') || (r >= 'a' && r <= 'f') || (r >= 'A' && r <= 'F')) {
			return false
		}
	}
	return true
}

func safeName(s string) string {
	var b strings.Builder
	for _, r := range s {
		if (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= '0' && r <= '9') {
			b.WriteRune(r)
		} else if b.Len() == 0 || !strings.HasSuffix(b.String(), "-") {
			b.WriteByte('-')
		}
	}
	out := strings.Trim(b.String(), "-")
	if out == "" {
		return "app"
	}
	return out
}

func setStatus(running bool, msg string, lines []string) {
	statusMu.Lock()
	defer statusMu.Unlock()
	status.Running = running
	status.Message = msg
	status.Log = lines
	status.WorkDir = workDir
}

func setRunning(running bool, msg string) {
	statusMu.Lock()
	defer statusMu.Unlock()
	status.Running = running
	status.Message = msg
}

func appendLog(line string) {
	statusMu.Lock()
	defer statusMu.Unlock()
	if len(status.Log) > 500 {
		status.Log = status.Log[len(status.Log)-500:]
	}
	status.Log = append(status.Log, time.Now().Format("15:04:05")+"  "+line)
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	_ = json.NewEncoder(w).Encode(v)
}

func openBrowser(url string) {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	case "darwin":
		cmd = exec.Command("open", url)
	default:
		cmd = exec.Command("xdg-open", url)
	}
	_ = cmd.Start()
}

func init() {
	_ = mime.AddExtensionType(".apk", "application/vnd.android.package-archive")
}

const indexHTML = `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A6000 Clean Installer</title>
<style>
:root{font-family:Segoe UI,Microsoft YaHei,Arial,sans-serif;color:#17202a;background:#f5f7f8}
body{margin:0}
header{background:#12212f;color:white;padding:18px 24px}
.head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;max-width:1280px;margin:0 auto}
h1{font-size:20px;margin:0 0 4px}
header p{margin:0;color:#b8c7d3;font-size:13px}
main{display:grid;grid-template-columns:minmax(360px,1fr) 430px;gap:18px;padding:18px;max-width:1280px;margin:0 auto}
.toolbar,.panel,.guide{background:white;border:1px solid #d9e0e6;border-radius:8px}
.toolbar{grid-column:1/-1;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;gap:14px}
.controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
select,button,input{font:inherit}
select,input{padding:7px 8px;border:1px solid #c9d2da;border-radius:6px;background:white}
input{min-width:min(520px,82vw)}
button{border:0;border-radius:6px;padding:8px 11px;background:#1769aa;color:white;cursor:pointer}
button:disabled{background:#aab5bf;cursor:not-allowed}
.ghost{background:#e8eef3;color:#183247}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.app{background:white;border:1px solid #d9e0e6;border-radius:8px;padding:12px;display:flex;flex-direction:column;gap:8px;min-height:184px}
.app h2{font-size:15px;margin:0;color:#12212f}
.meta{font-size:12px;color:#5e6b76;line-height:1.35;word-break:break-word}
.badge{display:inline-block;border-radius:999px;padding:3px 8px;font-size:12px;background:#e8f4ed;color:#166534}
.badge.warn{background:#fff3d6;color:#875800}
.badge.remote{background:#e7f0ff;color:#1d4ed8}
.app button{align-self:flex-start;margin-top:auto}
.side{position:sticky;top:12px;height:calc(100vh - 60px);display:flex;flex-direction:column;gap:12px}
.panel,.guide{padding:12px}
.panel{min-height:220px;display:flex;flex-direction:column;flex:1}
.panel h2,.guide h2{font-size:15px;margin:0 0 8px}
.guide ol{margin:8px 0 0 20px;padding:0;font-size:13px;line-height:1.55;color:#304252}
.guide code{background:#eef3f6;border-radius:4px;padding:1px 4px}
#log{background:#101820;color:#d9f2e6;border-radius:6px;padding:10px;overflow:auto;white-space:pre-wrap;font:12px Consolas,monospace;flex:1}
.status{font-size:13px;margin-bottom:8px;color:#304252}
@media(max-width:900px){main{grid-template-columns:1fr}.side{position:static;height:auto}.panel{height:360px}.toolbar{align-items:flex-start;flex-direction:column}.head{flex-direction:column}}
</style>
</head>
<body>
<header>
<div class="head">
<div>
<h1>A6000 Clean Installer</h1>
<p data-i18n="subtitle">PMCA 安装器：默认加载公开远程清单，无 Sony Market 登录，无易语言密码外壳。</p>
</div>
<button id="lang" class="ghost" onclick="toggleLang()">English</button>
</div>
</header>
<main>
<section class="toolbar">
<div class="controls">
<label><span data-i18n="driver">USB 驱动</span> <select id="driver"><option value="">auto</option><option value="native">native</option><option value="libusb">libusb</option></select></label>
<button class="ghost" onclick="window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'})" data-i18n="showGuide">查看教程</button>
</div>
<span class="meta" data-i18n="hint">Windows 需要 Python 3；首次安装会自动检查并安装 PMCA 依赖。</span>
</section>
<section class="toolbar">
<div class="controls">
<input id="catalogUrl" placeholder="https://example.com/a6000-catalog.json">
<button onclick="loadCatalog()" data-i18n="loadCatalog">加载远程清单</button>
</div>
<span class="meta" data-i18n="catalogHint">远程清单必须包含 downloadUrl 和 sha256；安装前会自动下载并校验。</span>
</section>
<section>
<div id="apps" class="grid"></div>
</section>
<aside class="side">
<section class="guide">
<h2 data-i18n="guideTitle">安装教程</h2>
<ol id="guide"></ol>
</section>
<section class="guide">
<h2 data-i18n="langTitle">应用中文支持</h2>
<ol id="localeSummary"></ol>
</section>
<section class="panel">
<h2 data-i18n="statusTitle">状态</h2>
<div id="state" class="status">空闲</div>
<pre id="log"></pre>
</section>
</aside>
</main>
<script>
let currentLang=localStorage.getItem('lang')||'zh';
let appCache=[];
const dict={
 zh:{
  subtitle:'PMCA 安装器：默认加载公开远程清单，无 Sony Market 登录，无易语言密码外壳。',
  driver:'USB 驱动',
  showGuide:'查看教程',
  hint:'Windows 需要 Python 3；首次安装会自动检查并安装 PMCA 依赖。',
  guideTitle:'安装教程',
  langTitle:'应用中文支持',
  statusTitle:'状态',
  install:'安装',
  loadCatalog:'加载远程清单',
  catalogHint:'远程清单必须包含 downloadUrl 和 sha256；安装前会自动下载并校验。',
  remote:'远程下载',
  embedded:'本地内置',
  package:'包名',
  version:'版本',
  file:'文件',
  size:'大小',
  chineseYes:'中文：已声明 zh 资源',
  chineseNo:'中文：未声明 zh 资源',
  locales:'语言资源',
  idle:'空闲',
  running:'运行中',
  steps:[
   '在 Windows 安装 Python 3。',
   '首次点击安装时，程序会自动检查 certifi、comtypes、pycryptodome、pyusb、pyyaml，缺失时自动调用 pip 安装。',
   '用 USB 连接 Sony A6000，并按相机提示保持连接。',
   '驱动先选 auto；失败后再试 native 或 libusb。',
   '点击应用卡片上的“安装”，右侧日志会显示 PMCA 输出。',
   '安装完成后，到相机的应用列表里检查。'
  ],
  localeSummary:[
   '公开版不内置 Sony 官方 APK；默认清单目前只包含可公开引用的 Recipe Lab。',
   'Recipe Lab v1.9.0 只声明 default；是否显示中文取决于它自身默认 UI。',
   '远程清单建议托管在静态 HTTPS 地址，APK 建议放在支持直链的 Releases、对象存储或 CDN。',
   '如果维护私有 Sony 应用清单，请自行确认 APK 的来源和分发权限。'
  ]
 },
 en:{
  subtitle:'PMCA installer with a public remote catalog by default. No Sony Market login or bundled outer password gate.',
  driver:'USB driver',
  showGuide:'Guide',
  hint:'Requires Python 3 on Windows. PMCA dependencies are checked and installed automatically.',
  guideTitle:'Install Guide',
  langTitle:'Chinese Locale Notes',
  statusTitle:'Status',
  install:'Install',
  loadCatalog:'Load remote catalog',
  catalogHint:'Remote catalog must include downloadUrl and sha256. The APK is downloaded and verified before install.',
  remote:'Remote download',
  embedded:'Bundled local',
  package:'Package',
  version:'Version',
  file:'File',
  size:'Size',
  chineseYes:'Chinese: zh resources declared',
  chineseNo:'Chinese: no zh resources declared',
  locales:'Locales',
  idle:'Idle',
  running:'Running',
  steps:[
   'Install Python 3 on Windows.',
   'On first install, the app checks certifi, comtypes, pycryptodome, pyusb, and pyyaml, then installs missing packages with pip.',
   'Connect the Sony A6000 over USB and keep it connected.',
   'Start with driver auto; try native or libusb if auto fails.',
   'Click Install on an app card. PMCA output appears in the log.',
   'After completion, check the camera application list.'
  ],
  localeSummary:[
   'The public build does not bundle Sony official APKs. The default catalog currently includes Recipe Lab only.',
   'Recipe Lab v1.9.0 declares only default; Chinese UI depends on its own default content.',
   'Host remote catalogs on static HTTPS. APK files should live on direct-link Releases, object storage, or CDN.',
   'If you maintain a private Sony app catalog, verify your APK source and redistribution rights.'
  ]
 }
};
async function json(url, opts){const r=await fetch(url, opts); if(!r.ok) throw new Error(await r.text()); return r.json();}
async function load(){
  appCache=await json('/api/apps');
  render();
}
async function loadCatalog(){
  const url=document.getElementById('catalogUrl').value.trim();
  if(!url){alert(currentLang==='zh'?'请输入远程清单 URL':'Enter a remote catalog URL');return;}
  try{
    await json('/api/catalog',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});
    appCache=await json('/api/apps');
    render();
  }catch(e){alert(e.message);}
}
function render(){
  const t=dict[currentLang];
  document.documentElement.lang=currentLang==='zh'?'zh-CN':'en';
  document.getElementById('lang').textContent=currentLang==='zh'?'English':'中文';
  document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t[el.getAttribute('data-i18n')];});
  document.getElementById('guide').innerHTML=t.steps.map(s=>'<li>'+escapeHtml(s)+'</li>').join('');
  document.getElementById('localeSummary').innerHTML=t.localeSummary.map(s=>'<li>'+escapeHtml(s)+'</li>').join('');
  document.getElementById('apps').innerHTML=appCache.map(app=>card(app,t)).join('');
}
function card(app,t){
  const badge=app.chinese?'<span class="badge">'+t.chineseYes+'</span>':'<span class="badge warn">'+t.chineseNo+'</span>';
  const source=app.source==='remote'?'<span class="badge remote">'+t.remote+'</span>':'<span class="badge">'+t.embedded+'</span>';
  const locales=(app.locales||[]).slice(0,10).join(', ')+((app.locales||[]).length>10?' ...':'');
  return '<article class="app">'+
    '<h2>'+escapeHtml(app.id)+'. '+escapeHtml(app.name)+'</h2>'+
    '<div>'+source+' '+badge+'</div>'+
    '<div class="meta">'+t.package+': '+escapeHtml(app.package||'-')+'</div>'+
    '<div class="meta">'+t.version+': '+escapeHtml(app.versionName||'-')+'</div>'+
    '<div class="meta">'+t.file+': '+escapeHtml(app.file)+'</div>'+
    '<div class="meta">'+t.size+': '+(app.size/1024/1024).toFixed(2)+' MB · SHA256 '+escapeHtml(app.sha256.slice(0,12))+'</div>'+
    '<div class="meta">'+t.locales+': '+escapeHtml(locales||'-')+'</div>'+
    '<div class="meta">'+escapeHtml(app.note)+'</div>'+
    '<button onclick="installApp(\''+escapeHtml(app.id)+'\')">'+t.install+'</button>'+
    '</article>';
}
function toggleLang(){
  currentLang=currentLang==='zh'?'en':'zh';
  localStorage.setItem('lang',currentLang);
  render();
}
async function installApp(id){
  const driver=document.getElementById('driver').value;
  try{await json('/api/install',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,driver})});}
  catch(e){alert(e.message);}
}
async function poll(){
  try{
    const s=await json('/api/status');
    const t=dict[currentLang];
    document.getElementById('state').textContent=s.message || (s.running?t.running:t.idle);
    document.getElementById('log').textContent=(s.log||[]).join('\n');
  }catch(e){}
  setTimeout(poll,1000);
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
load(); poll();
</script>
</body>
</html>`
