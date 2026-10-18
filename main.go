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
	DisplayName string   `json:"displayName,omitempty"`
	EnglishName string   `json:"englishName,omitempty"`
	Description string   `json:"description,omitempty"`
	Tags        []string `json:"tags,omitempty"`
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

type preflightRequest struct {
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

type appMetadata struct {
	DisplayName string
	EnglishName string
	Description string
	Tags        []string
}

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

var embeddedAppMetadata = map[string]appMetadata{
	"01": {
		DisplayName: "角度偏移插件",
		EnglishName: "Timelapse add-on",
		Description: "延时摄影的附加组件，把延时照片生成带有平移、倾斜、缩放效果的视频。",
		Tags:        []string{"延时摄影", "视频生成", "运镜"},
	},
	"02": {
		DisplayName: "延时摄影",
		EnglishName: "Time-lapse",
		Description: "按固定间隔自动拍摄一组照片，适合云流动、日落、城市车流、植物生长等场景。",
		Tags:        []string{"延时摄影", "间隔拍摄", "风光"},
	},
	"03": {
		DisplayName: "平滑反射",
		EnglishName: "Smooth Reflection",
		Description: "通过连续拍摄并合成，模拟长曝光效果，让水面、云层、人流等运动画面变得更平滑。",
		Tags:        []string{"长曝光", "风光", "水面"},
	},
	"04": {
		DisplayName: "实时取景调色",
		EnglishName: "Liveview Grading",
		Description: "在拍摄时套用不同的色彩风格预设，方便预览并拍出偏电影感或特殊色调的照片。",
		Tags:        []string{"调色", "滤镜", "预设"},
	},
	"05": {
		DisplayName: "光绘",
		EnglishName: "Light Graffiti",
		Description: "用于拍摄光轨、光绘文字和夜景创意效果，适合手电、车灯、烟花等移动光源。",
		Tags:        []string{"光绘", "夜景", "长曝光"},
	},
	"06": {
		DisplayName: "包围曝光工具",
		EnglishName: "Bracket Pro",
		Description: "连续拍摄不同焦点、光圈、闪光等参数的照片，方便后期做景深合成或选择最佳曝光。",
		Tags:        []string{"包围曝光", "对焦包围", "后期合成"},
	},
	"07": {
		DisplayName: "美颜效果",
		EnglishName: "Beauty Effect",
		Description: "针对人像照片做皮肤、亮度和脸部效果优化，适合直接在相机里快速处理人像。",
		Tags:        []string{"人像", "美颜", "机内处理"},
	},
	"08": {
		DisplayName: "定格动画",
		EnglishName: "Stop Motion",
		Description: "辅助逐帧拍摄并制作定格动画，适合玩具、模型、产品小动画等创作。",
		Tags:        []string{"定格动画", "逐帧", "视频创作"},
	},
	"09": {
		DisplayName: "照片润饰",
		EnglishName: "Photo Retouch / EZ Edit",
		Description: "在相机内对照片做基础编辑和润饰，例如裁切、亮度、色彩或简单效果处理。",
		Tags:        []string{"照片编辑", "机内处理", "修图"},
	},
	"10": {
		DisplayName: "渐变滤镜",
		EnglishName: "Graduated Filter",
		Description: "模拟渐变 ND 或渐变色滤镜，常用于压暗天空、平衡明暗反差、强化风光层次。",
		Tags:        []string{"风光", "渐变滤镜", "明暗控制"},
	},
	"11": {
		DisplayName: "手动镜头补偿",
		EnglishName: "Manual Lens Compensation",
		Description: "给手动镜头或无电子触点镜头设置暗角、畸变、色差等补偿参数。",
		Tags:        []string{"手动镜头", "镜头补偿", "画质修正"},
	},
	"12": {
		DisplayName: "照片效果+",
		EnglishName: "Picture Effect+",
		Description: "扩展相机内置创意效果，拍摄时直接应用更多风格化滤镜。",
		Tags:        []string{"创意滤镜", "照片效果", "直出"},
	},
	"13": {
		DisplayName: "免触快门",
		EnglishName: "Touchless Shutter",
		Description: "通过遮挡或挥手触发快门，减少按快门造成的机身震动，适合三脚架和长曝光。",
		Tags:        []string{"免触发", "防抖", "长曝光"},
	},
	"14": {
		DisplayName: "光束效果",
		EnglishName: "Light Shaft",
		Description: "给照片添加或强化光束、光线穿透等效果，适合逆光、舞台、森林光线类画面。",
		Tags:        []string{"光效", "创意滤镜", "氛围"},
	},
	"15": {
		DisplayName: "多重曝光",
		EnglishName: "Multiple Exposure",
		Description: "把多张照片叠加成一张，做出重影、剪影叠加、创意合成等多重曝光效果。",
		Tags:        []string{"多重曝光", "创意合成", "人像"},
	},
	"16": {
		DisplayName: "智能遥控",
		EnglishName: "Smart Remote Control",
		Description: "让手机或电脑连接相机进行远程取景、调整参数和触发拍摄。",
		Tags:        []string{"遥控拍摄", "手机连接", "远程取景"},
	},
	"17": {
		DisplayName: "动态拍摄",
		EnglishName: "Motion Shot",
		Description: "把连续运动过程合成为一张照片，表现人物、运动、宠物等主体的移动轨迹。",
		Tags:        []string{"运动轨迹", "连拍合成", "创意"},
	},
	"18": {
		DisplayName: "星轨",
		EnglishName: "Star Trail",
		Description: "连续拍摄并合成星空轨迹，适合夜空、银河和长时间星轨创作。",
		Tags:        []string{"星空", "星轨", "夜景"},
	},
	"19": {
		DisplayName: "数字滤镜",
		EnglishName: "Digital Filter",
		Description: "在同一张照片的不同区域应用不同效果，适合风光、人像和创意滤镜叠加。",
		Tags:        []string{"滤镜", "区域效果", "创意"},
	},
	"20": {
		DisplayName: "肖像布光",
		EnglishName: "Portrait Lighting",
		Description: "给人像照片模拟不同布光效果，改善面部光线和整体人像氛围。",
		Tags:        []string{"人像", "布光", "机内处理"},
	},
	"21": {
		DisplayName: "Recipe Lab 创意配方",
		EnglishName: "Recipe Lab",
		Description: "第三方开源应用，用于在相机里管理和应用照片风格配方，方便快速切换不同直出风格。",
		Tags:        []string{"第三方", "开源", "色彩配方"},
	},
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
	mux.HandleFunc("/api/preflight", handlePreflight)
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
	if !ok || cfg.CatalogURL == "" {
		return
	}
	remote, err := loadRemoteCatalog(cfg.CatalogURL)
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
	applyEmbeddedMetadata(items)
	return items, nil
}

func applyEmbeddedMetadata(items []appItem) {
	for i := range items {
		meta, ok := embeddedAppMetadata[items[i].ID]
		if !ok {
			continue
		}
		items[i].DisplayName = meta.DisplayName
		items[i].EnglishName = meta.EnglishName
		items[i].Description = meta.Description
		items[i].Tags = append([]string(nil), meta.Tags...)
	}
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

func handlePreflight(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	var req preflightRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	if req.Driver != "" && req.Driver != "native" && req.Driver != "libusb" {
		http.Error(w, "driver must be native, libusb, or empty", http.StatusBadRequest)
		return
	}
	if !installMu.TryLock() {
		http.Error(w, "another install or check is running", http.StatusConflict)
		return
	}
	setStatus(true, "Checking environment and camera", nil)
	go func() {
		defer installMu.Unlock()
		err := runFullPreflight(req.Driver)
		if err != nil {
			appendLog("ERROR: " + err.Error())
			setRunning(false, "Check failed")
			return
		}
		setRunning(false, "Check passed")
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
	pmcaDir := filepath.Join(workDir, "pmca")
	python, args, err := preparePythonRuntime()
	if err != nil {
		return err
	}
	if err := runCameraPreflight(python, args, pmcaDir, driver); err != nil {
		return err
	}
	apk, err := resolveAPK(item)
	if err != nil {
		return err
	}
	cmdArgs := append(args, "pmca-console.py", "install")
	if driver != "" {
		cmdArgs = append(cmdArgs, "-d", driver)
	}
	cmdArgs = append(cmdArgs, "-f", apk)
	appendLog("Command: " + python + " " + strings.Join(cmdArgs, " "))
	appendLog("Tip: connect the camera by USB and put it in the required install mode.")
	out, err := runPMCA(python, cmdArgs, pmcaDir)
	outText := string(out)
	for _, line := range strings.Split(strings.ReplaceAll(outText, "\r\n", "\n"), "\n") {
		if strings.TrimSpace(line) != "" {
			appendLog(line)
		}
	}
	if err != nil {
		appendPMCAHints(outText)
		appendLog("If Python dependencies are missing, run:")
		appendLog(pythonCommand(python, args, "-m", "pip", "install", "--user", "--upgrade", "certifi", "comtypes", "pycryptodome", "pyusb", "pyyaml"))
		return err
	}
	return nil
}

func runFullPreflight(driver string) error {
	pmcaDir := filepath.Join(workDir, "pmca")
	python, args, err := preparePythonRuntime()
	if err != nil {
		return err
	}
	return runCameraPreflight(python, args, pmcaDir, driver)
}

func preparePythonRuntime() (string, []string, error) {
	python, args, err := findPython()
	if err != nil {
		return "", nil, err
	}
	appendLog("Python: " + python)
	if err := ensurePythonDependencies(python, args); err != nil {
		return "", nil, err
	}
	return python, args, nil
}

func runCameraPreflight(python string, args []string, pmcaDir, driver string) error {
	cmdArgs := append(args, "pmca-console.py", "info")
	if driver != "" {
		cmdArgs = append(cmdArgs, "-d", driver)
	}
	appendLog("Checking camera connection...")
	appendLog("Command: " + python + " " + strings.Join(cmdArgs, " "))
	out, err := runPMCA(python, cmdArgs, pmcaDir)
	outText := string(out)
	for _, line := range strings.Split(strings.ReplaceAll(outText, "\r\n", "\n"), "\n") {
		if strings.TrimSpace(line) != "" {
			appendLog(line)
		}
	}
	if err != nil {
		appendPMCAHints(outText)
		return fmt.Errorf("camera preflight failed: %w", err)
	}
	appendLog("Camera preflight: OK")
	return nil
}

func runPMCA(python string, cmdArgs []string, pmcaDir string) ([]byte, error) {
	cmd := exec.Command(python, cmdArgs...)
	cmd.Dir = pmcaDir
	cmd.Env = append(os.Environ(), "PYTHONIOENCODING=utf-8")
	return cmd.CombinedOutput()
}

func appendPMCAHints(output string) {
	lower := strings.ToLower(output)
	if strings.Contains(lower, "no module named") || strings.Contains(lower, "modulenotfounderror") {
		appendLog("提示：Python 运行模块缺失。完整版会优先使用内置 Python；如果你设置了 A6000_PYTHON，请确认它能导入 PMCA 依赖。")
	}
	if strings.Contains(lower, "unknown location") {
		appendLog("提示：相机返回 Unknown location，通常是安装任务里的下载地址被相机拒绝。此版本已改为给相机官方域名地址；如果仍出现，请重启相机后再试。")
		appendLog("建议：相机 USB 连接模式设为 MTP 或 Auto，关闭相机 Wi-Fi，Windows 防火墙允许本程序和 Python 访问本机网络。")
	}
	if strings.Contains(lower, "communication error") || strings.Contains(lower, "response error") {
		appendLog("提示：相机安装任务返回通信错误。请确认相机电量充足、存储空间足够，并重启相机后重试。")
	}
	if strings.Contains(lower, "no devices found") {
		appendLog("提示：没有检测到 Sony 相机。请检查 USB 线、相机开机状态，并在相机菜单里把 USB 连接设为 MTP 或 Auto。")
	}
	if strings.Contains(lower, "too many devices") {
		appendLog("提示：检测到多个 Sony USB 设备。安装时只连接一台相机。")
	}
	if strings.Contains(lower, "operation timed out") {
		appendLog("提示：相机切换到应用安装模式超时。请等待相机重新连接完成后，再点一次安装。")
	}
	if strings.Contains(lower, "device busy") || strings.Contains(lower, "resource busy") {
		appendLog("提示：相机或 USB 设备正忙。请关闭 Imaging Edge、照片导入工具、资源管理器里的相机窗口后重试。")
	}
	if strings.Contains(lower, "address already in use") || strings.Contains(lower, "only one usage of each socket address") {
		appendLog("提示：本地安装服务端口被占用。请关闭其他 PMCA/安装器窗口后重新打开本程序。")
	}
	if strings.Contains(lower, "ssl") || strings.Contains(lower, "certificate") {
		appendLog("提示：相机和本地安装服务的 HTTPS 通信失败。请关闭代理/VPN，允许本程序和内置 Python 访问本机网络。")
	}
	if strings.Contains(lower, "timed out") || strings.Contains(lower, "timeout") {
		appendLog("提示：通信超时。请换一根 USB 数据线或 USB 口，保持相机开机，不要让相机进入休眠。")
	}
	if strings.Contains(lower, "access denied") || strings.Contains(lower, "permission") {
		appendLog("提示：USB 访问权限不足。Windows 上可尝试换 USB 口、关闭占用相机的软件，或用控制台版查看完整错误。")
	}
	if strings.Contains(lower, "low battery") {
		appendLog("提示：相机电量不足。请充电或接外部供电后再安装。")
	}
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
	if runtime.GOOS == "windows" {
		p := filepath.Join(workDir, "runtime", "python-win64", "python.exe")
		if _, err := os.Stat(p); err == nil {
			appendLog("Using bundled Python runtime.")
			return p, nil, nil
		}
		appendLog("Bundled Python runtime was not found; falling back to system Python.")
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
	return "", nil, errors.New("Python was not found. This build should include a bundled Python runtime; download the latest full release or set A6000_PYTHON to a Python 3 executable")
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
.alias{font-size:12px;color:#6c7781;margin-top:-4px}
.desc{font-size:13px;color:#263846;line-height:1.45}
.meta{font-size:12px;color:#5e6b76;line-height:1.35;word-break:break-word}
.badge{display:inline-block;border-radius:999px;padding:3px 8px;font-size:12px;background:#e8f4ed;color:#166534}
.badge.warn{background:#fff3d6;color:#875800}
.badge.remote{background:#e7f0ff;color:#1d4ed8}
.tag{display:inline-block;border:1px solid #d5dde5;border-radius:999px;padding:2px 7px;font-size:12px;color:#304252;background:#f7fafc;margin:0 4px 4px 0}
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
<p data-i18n="subtitle">离线 PMCA 安装器：无 Sony Market 登录，无易语言密码外壳。</p>
</div>
<button id="lang" class="ghost" onclick="toggleLang()">English</button>
</div>
</header>
<main>
<section class="toolbar">
<div class="controls">
<label><span data-i18n="driver">USB 驱动</span> <select id="driver"><option value="">auto</option><option value="native">native</option><option value="libusb">libusb</option></select></label>
<button onclick="runPreflight()" data-i18n="preflight">检测环境/相机</button>
<button class="ghost" onclick="window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'})" data-i18n="showGuide">查看教程</button>
</div>
<span class="meta" data-i18n="hint">Windows 完整版已内置 Python 运行时；安装前可先检测环境和相机。</span>
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
	  subtitle:'离线 PMCA 安装器：无 Sony Market 登录，无易语言密码外壳。',
	  driver:'USB 驱动',
	  preflight:'检测环境/相机',
	  showGuide:'查看教程',
	  hint:'Windows 完整版已内置 Python 运行时；安装前可先检测环境和相机。',
  guideTitle:'安装教程',
  langTitle:'应用中文支持',
  statusTitle:'状态',
  install:'安装',
  loadCatalog:'加载远程清单',
  catalogHint:'远程清单必须包含 downloadUrl 和 sha256；安装前会自动下载并校验。',
  remote:'远程下载',
  embedded:'内置离线',
  package:'包名',
	  version:'版本',
	  alias:'英文名',
	  description:'用途',
	  tags:'标签',
	  file:'文件',
  size:'大小',
  chineseYes:'中文：已声明 zh 资源',
  chineseNo:'中文：未声明 zh 资源',
  locales:'语言资源',
  idle:'空闲',
  running:'运行中',
		steps:[
	   'Windows 完整版已内置 Python 运行时，通常不需要另装 Python。',
	   '如果使用自定义 Python，程序仍会检查 certifi、comtypes、pycryptodome、pyusb、pyyaml。',
	   '用 USB 连接 Sony A6000；相机菜单里的 USB 连接建议设为 MTP 或 Auto。',
	   '可以先点击“检测环境/相机”；安装时也会自动做同样的预检。',
	   '驱动先选 auto；失败后再试 native 或 libusb。',
	   '如果日志提示 Unknown location，先重启相机，关闭相机 Wi-Fi，再重新点击安装。',
	   '点击应用卡片上的“安装”，右侧日志会显示 PMCA 输出。',
	   '安装完成后，到相机的应用列表里检查。'
  ],
  localeSummary:[
   '已解析 APK resources.arsc 的 locale 声明。',
   '原始 Sony 包中多数包含 zh 资源；Touchless Shutter 只声明 default/ja。',
   'Recipe Lab v1.9.0 只声明 default；是否显示中文取决于它自身默认 UI。',
   '远程清单建议托管在静态 HTTPS 地址，APK 建议放在支持直链的 Releases、对象存储或 CDN。'
  ]
 },
 en:{
	  subtitle:'Offline PMCA installer: no Sony Market login and no bundled outer password gate.',
	  driver:'USB driver',
	  preflight:'Check environment/camera',
	  showGuide:'Guide',
	  hint:'The full Windows build includes a bundled Python runtime. You can check the environment and camera before installing.',
  guideTitle:'Install Guide',
  langTitle:'Chinese Locale Notes',
  statusTitle:'Status',
  install:'Install',
  loadCatalog:'Load remote catalog',
  catalogHint:'Remote catalog must include downloadUrl and sha256. The APK is downloaded and verified before install.',
  remote:'Remote download',
  embedded:'Embedded offline',
  package:'Package',
	  version:'Version',
	  alias:'Alias',
	  description:'Description',
	  tags:'Tags',
	  file:'File',
  size:'Size',
  chineseYes:'Chinese: zh resources declared',
  chineseNo:'Chinese: no zh resources declared',
  locales:'Locales',
  idle:'Idle',
  running:'Running',
		steps:[
	   'The full Windows build bundles Python, so a separate Python install is usually not needed.',
	   'If you override Python, the app still checks certifi, comtypes, pycryptodome, pyusb, and pyyaml.',
	   'Connect the Sony A6000 over USB. Set the camera USB connection mode to MTP or Auto.',
	   'Click Check environment/camera first if needed. Install also runs the same preflight automatically.',
	   'Start with driver auto; try native or libusb if auto fails.',
	   'If the log says Unknown location, restart the camera, disable camera Wi-Fi, then retry the install.',
	   'Click Install on an app card. PMCA output appears in the log.',
	   'After completion, check the camera application list.'
  ],
  localeSummary:[
   'Locale declarations are parsed from each APK resources.arsc.',
   'Most original Sony packages declare zh resources; Touchless Shutter declares only default/ja.',
   'Recipe Lab v1.9.0 declares only default; Chinese UI depends on its own default content.',
   'Host remote catalogs on static HTTPS. APK files should live on direct-link Releases, object storage, or CDN.'
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
  const title=app.displayName||app.name;
  const alias=app.englishName||((app.displayName&&app.displayName!==app.name)?app.name:'');
  const tags=(app.tags||[]).map(tag=>'<span class="tag">'+escapeHtml(tag)+'</span>').join('');
  const note=(app.source==='remote'&&app.note)?'<div class="meta">'+escapeHtml(app.note)+'</div>':'';
  return '<article class="app">'+
    '<h2>'+escapeHtml(app.id)+'. '+escapeHtml(title)+'</h2>'+
    (alias?'<div class="alias">'+t.alias+': '+escapeHtml(alias)+'</div>':'')+
    '<div>'+source+' '+badge+'</div>'+
    (app.description?'<div class="desc">'+escapeHtml(app.description)+'</div>':'')+
    (tags?'<div>'+tags+'</div>':'')+
    '<div class="meta">'+t.package+': '+escapeHtml(app.package||'-')+'</div>'+
    '<div class="meta">'+t.version+': '+escapeHtml(app.versionName||'-')+'</div>'+
    '<div class="meta">'+t.file+': '+escapeHtml(app.file)+'</div>'+
    '<div class="meta">'+t.size+': '+(app.size/1024/1024).toFixed(2)+' MB · SHA256 '+escapeHtml(app.sha256.slice(0,12))+'</div>'+
    '<div class="meta">'+t.locales+': '+escapeHtml(locales||'-')+'</div>'+
    note+
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
async function runPreflight(){
  const driver=document.getElementById('driver').value;
  try{await json('/api/preflight',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({driver})});}
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
