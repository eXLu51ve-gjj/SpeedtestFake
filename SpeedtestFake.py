#!/usr/bin/env python3
import time, sys, os
import tkinter as tk
from tkinter import messagebox

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
except ImportError:
    root = tk.Tk(); root.withdraw()
    messagebox.showerror("Ошибка", "Selenium не установлен"); sys.exit(1)

class ConfigWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Speedtest Fake")
        self.geometry("550x420")
        self.resizable(False, False)
        self.configure(bg="#0f1419")
        
        # Иконка окна
        try:
            self.iconbitmap('speedtest_icon.ico')
        except:
            pass
        
        x = (self.winfo_screenwidth() // 2) - 275
        y = (self.winfo_screenheight() // 2) - 210
        self.geometry(f"550x500+{x}+{y}")
        self.config_data = None
        self._build()

    def _build(self):
        # Заголовок
        header = tk.Frame(self, bg="#1a1f2e", height=100)
        header.pack(fill="x", pady=(0, 30))
        
        tk.Label(header, text="⚡ Speedtest Fake", font=("Segoe UI", 22, "bold"), 
                 bg="#1a1f2e", fg="#00d4ff").pack(pady=(15, 4))
        tk.Label(header, text="by eXLu51ve", font=("Segoe UI", 11, "italic"), 
                 bg="#1a1f2e", fg="#6b7280").pack(pady=(0, 15))

        # Контейнер для полей
        container = tk.Frame(self, bg="#0f1419")
        container.pack(expand=True, fill="both", padx=40, pady=10)

        def make_field(parent, label, default, hint, col, row):
            frame = tk.Frame(parent, bg="#0f1419")
            frame.grid(row=row, column=col, padx=10, pady=8, sticky="nsew")
            tk.Label(frame, text=label, font=("Segoe UI", 10, "bold"),
                     bg="#0f1419", fg="#e5e7eb", anchor="w").pack(fill="x")
            v = tk.StringVar(value=default)
            tk.Entry(frame, textvariable=v, font=("Segoe UI", 11),
                     bg="#1f2937", fg="#ffffff", relief="flat",
                     insertbackground="#00d4ff", bd=0).pack(fill="x", ipady=8, pady=(4,2))
            tk.Label(frame, text=hint, font=("Segoe UI", 8),
                     bg="#0f1419", fg="#6b7280", anchor="w").pack(fill="x")
            return v

        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

        self.vars = [
            make_field(container, "Префикс скорости:", "11", "11 → 11500 Mbps", 0, 0),
            make_field(container, "Ping (ms):",        "",   "Пусто = реальный",  1, 0),
            make_field(container, "IP адрес:",         "",   "Пусто = реальный",  0, 1),
            make_field(container, "Провайдер:",        "",   "Пусто = реальный",  1, 1),
        ]

        # Кнопка запуска
        btn_frame = tk.Frame(self, bg="#0f1419")
        btn_frame.pack(pady=15)
        
        btn = tk.Button(btn_frame, text="🚀  Запустить", font=("Segoe UI", 13, "bold"), 
                       bg="#00d4ff", fg="#0f1419", activebackground="#00b8e6", 
                       activeforeground="#0f1419", relief="flat", bd=0,
                       command=self._start, cursor="hand2", width=25, height=2)
        btn.pack()

    def _start(self):
        prefix = self.vars[0].get().strip()
        if not prefix:
            messagebox.showerror("Ошибка", "Префикс обязателен"); return
        self.config_data = {
            'prefix': prefix,
            'ping': self.vars[1].get().strip() or None,
            'ip': self.vars[2].get().strip() or None,
            'isp': self.vars[3].get().strip() or None,
        }
        self.destroy()


class SpeedtestModifier:
    def __init__(self, config):
        self.config = config
        self.driver = None

    def setup_browser(self):
        opts = Options()
        opts.add_argument('--disable-blink-features=AutomationControlled')
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_argument('--start-maximized')
        try:
            # Selenium 4.6+ автоматически скачивает ChromeDriver — не нужен webdriver_manager
            self.driver = webdriver.Chrome(options=opts)
            print("✅ Браузер запущен")
            return True
        except Exception as e:
            root = tk.Tk(); root.withdraw()
            messagebox.showerror("Ошибка браузера", f"Не удалось запустить Chrome:\n\n{e}\n\nУбедитесь что Google Chrome установлен.")
            return False

    def inject_modifier(self):
        p = self.config
        prefix    = p['prefix']
        fake_ping = f'"{p["ping"]}"'  if p['ping'] else 'null'
        fake_ip   = f'"{p["ip"]}"'   if p['ip']  else 'null'
        fake_isp  = f'"{p["isp"]}"'  if p['isp'] else 'null'

        js = f"""
(function() {{
    const PREFIX   = "{prefix}";
    const FAKE_PING = {fake_ping};
    const FAKE_IP   = {fake_ip};
    const FAKE_ISP  = {fake_isp};

    const SCALE = new Set([0, 5, 10, 50, 100, 250, 500, 750, 1000]);
    let testRunning = false;

    // ── Canvas: только спидометр ──────────────────────────────────
    const _fill   = CanvasRenderingContext2D.prototype.fillText;
    const _stroke = CanvasRenderingContext2D.prototype.strokeText;
    window.canvasModified = new Set(); // Отслеживаем что уже модифицировали

    function patchCanvas(text, y) {{
        const str = String(text);
        const n = parseFloat(str);
        if (isNaN(n) || SCALE.has(n)) return text;

        // ping-зона (y < 120)
        if (y < 120 && n >= 1 && n <= 300) {{
            return FAKE_PING !== null ? FAKE_PING : text;
        }}

        // скорость-зона (y >= 120)
        if (y >= 120 && testRunning && n > 0) {{
            const modified = PREFIX + str;
            window.canvasModified.add(modified); // Запоминаем
            console.log('Canvas:', str, '→', modified);
            return modified;
        }}
        return text;
    }}

    CanvasRenderingContext2D.prototype.fillText = function(t,x,y,mw) {{
        return _fill.call(this, patchCanvas(t,y), x, y, mw);
    }};
    CanvasRenderingContext2D.prototype.strokeText = function(t,x,y,mw) {{
        return _stroke.call(this, patchCanvas(t,y), x, y, mw);
    }};

    // ── textContent: HTML-элементы ────────────────────────────────
    const _tc = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');

    Object.defineProperty(Node.prototype, 'textContent', {{
        get() {{ return _tc.get.call(this); }},
        set(val) {{
            const cls    = (this.className || '').toLowerCase();
            const pCls   = (this.parentElement?.className || '').toLowerCase();
            const gpCls  = (this.parentElement?.parentElement?.className || '').toLowerCase();
            const str    = String(val);
            const n      = parseFloat(str.replace(/,/g,''));
            let out = val;

            // IP
            if (FAKE_IP && (cls.includes('js-data-ip') ||
                (cls.includes('result-data') && (pCls.includes('ispcomponent') || gpCls.includes('ispcomponent'))))) {{
                out = FAKE_IP;
                _tc.set.call(this, out); return;
            }}

            // ISP
            if (FAKE_ISP && (cls.includes('js-data-isp') ||
                (cls.includes('result-label') && (pCls.includes('ispcomponent') || gpCls.includes('ispcomponent'))))) {{
                out = FAKE_ISP;
                _tc.set.call(this, out); return;
            }}

            // Ping HTML
            if (cls.includes('ping-speed')) {{
                if (FAKE_PING && !isNaN(n)) out = FAKE_PING;
                _tc.set.call(this, out); return;
            }}

            // Метки шкалы — не трогаем
            if (cls.includes('increment') || pCls.includes('increment')) {{
                _tc.set.call(this, out); return;
            }}

            // Скорость (download-speed / upload-speed / result-data-large)
            if (!isNaN(n) && n > 0 &&
                (cls.includes('download-speed') || cls.includes('upload-speed') || cls.includes('result-data-large'))) {{
                
                const modified = PREFIX + str;
                
                // НЕ модифицируем если Canvas уже модифицировал это значение
                if (window.canvasModified && window.canvasModified.has(modified)) {{
                    console.log('HTML skip (Canvas already modified):', str);
                    _tc.set.call(this, out); return;
                }}
                
                // НЕ дублируем: если уже начинается с PREFIX — пропускаем
                if (!str.startsWith(PREFIX)) {{
                    out = modified;
                    console.log('HTML speed:', str, '→', out);
                }}
            }}

            _tc.set.call(this, out);
        }}
    }});

    // ── Мониторинг ────────────────────────────────────────────────
    let checkCount = 0;
    setInterval(() => {{
        checkCount++;
        const body = document.body?.textContent?.toLowerCase() || '';
        
        // Определяем состояние теста
        const isTesting = body.includes('testing') || body.includes('загрузка') || body.includes('выгрузка');
        if (!testRunning && isTesting) {{
            testRunning = true;
            console.log('🚀 Тест запущен');
        }}

        // IP/ISP/Ping - проверяем только каждые 500ms (каждый 2-й раз)
        if (checkCount % 2 === 0) {{
            if (FAKE_IP) {{
                document.querySelectorAll('.js-data-ip').forEach(el => {{
                    if (el.textContent !== FAKE_IP) el.textContent = FAKE_IP;
                }});
                document.querySelectorAll('.ispComponent .result-data').forEach(el => {{
                    if (el.textContent.includes('.') && el.textContent !== FAKE_IP) el.textContent = FAKE_IP;
                }});
            }}

            if (FAKE_ISP) {{
                document.querySelectorAll('.js-data-isp').forEach(el => {{
                    if (el.textContent !== FAKE_ISP) el.textContent = FAKE_ISP;
                }});
                document.querySelectorAll('.ispComponent .result-label').forEach(el => {{
                    if (el.textContent !== FAKE_ISP) el.textContent = FAKE_ISP;
                }});
            }}

            if (FAKE_PING) {{
                document.querySelectorAll('.ping-speed').forEach(el => {{
                    const n = parseFloat(el.textContent);
                    if (!isNaN(n) && el.textContent !== FAKE_PING) el.textContent = FAKE_PING;
                }});
            }}
        }}

        // ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ - проверяем всегда
        const results = document.querySelectorAll('.result-data-large.number.result-data-value');
        if (results.length > 0) {{
            results.forEach(el => {{
                const txt = el.textContent.trim();
                const num = parseFloat(txt.replace(/,/g, ''));
                
                if (!isNaN(num) && num > 0 && num < 10000 && !txt.startsWith(PREFIX)) {{
                    const modified = PREFIX + txt;
                    el.textContent = modified;
                    console.log('Final result:', txt, '→', modified);
                }}
            }});
        }}

    }}, 250);

    console.log('✅ Modifier ready. PREFIX=' + PREFIX);
}})();
"""
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': js})
        print(f"✅ Модификатор внедрён (PREFIX={prefix})")

    def open_speedtest(self):
        self.driver.get("https://www.speedtest.net")
        time.sleep(3)
        try:
            self.driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
            time.sleep(1)
        except: pass
        print("✅ Страница загружена")

    def run(self):
        # Просто держим браузер открытым пока пользователь его не закроет
        try:
            while True:
                time.sleep(1)
                # Проверяем что браузер ещё открыт
                try:
                    _ = self.driver.current_url
                except:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            try: self.driver.quit()
            except: pass


def main():
    w = ConfigWindow()
    w.mainloop()
    if not w.config_data: return

    m = SpeedtestModifier(w.config_data)
    if m.setup_browser():
        m.inject_modifier()
        m.open_speedtest()
        m.run()

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("Завершено")
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        try:
            root = tk.Tk(); root.withdraw()
            messagebox.showerror("Ошибка", err)
        except: pass
