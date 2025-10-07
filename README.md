# 日文影像 OCR 工具

這個專案提供一個命令列工具，透過 OpenAI Responses API 將影像中的日文文字辨識後輸出為 Markdown 檔案。

## 需求

- Python 3.10+
- 安裝 [`openai`](https://pypi.org/project/openai/) 套件：
  ```bash
  pip install openai
  ```
- 將 `OPENAI_API_KEY` 環境變數設定為你的 API 金鑰：
  - macOS / Linux（bash、zsh）：`export OPENAI_API_KEY=你的金鑰`
  - Windows PowerShell：`$env:OPENAI_API_KEY = "你的金鑰"`
  - Windows 命令提示字元 (CMD)：`set OPENAI_API_KEY=你的金鑰`

## 使用方式

```bash
python ocr_japanese.py path/to/image1.png /path/to/book_scans -o ./output
```

- `path/to/image*.png`：要進行 OCR 的影像路徑，可以一次提供多個。Windows 使用者也可以直接在命令列輸入萬用字元（例如 `*.png`），程式會自動展開對應的檔案。
- `/path/to/book_scans`：如果改提供目錄，程式會自動偵測其中所有支援的影像檔（依數字順序排序），並將辨識結果合併輸出成單一 Markdown 檔案，檔名為目錄名稱。
- `-o/--output-dir`：指定輸出資料夾，預設為 `./ocr_output`。
- `--model`：可選擇不同的 OpenAI 模型，預設為 `gpt-4.1-mini`。

對於單張影像，程式會產生對應檔名的 `.md` 檔案；對於目錄，會產生合併後的單一 Markdown。
