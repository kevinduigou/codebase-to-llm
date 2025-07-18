# 📘 Desktop Context Copier — User Manual

**Purpose:** This tool helps you craft effective, high-quality context for LLM-assisted coding by allowing you to curate, structure, and export codebase information (files, snippets, and rules) to your clipboard. Paste this context into any LLM interface (e.g., ChatGPT, Claude, or Cursor) to improve response relevance and coding performance.

---

## 🚀 Quick Start

1. **Launch the app**.
2. **Select a root directory** via the **📂 Choose Directory** button or pick from
   the **📁 Open Recently** menu. Click **🔍 Refresh View** if the file tree needs updating.
3. **Drag files or select snippets** from the preview panel into the **Context Buffer**.
4. **Add external sources** via the **Add External Source** button to include web pages or YouTube transcripts.
5. **Use "Add as Prompt** by right-clicking a file in the tree to fill the prompt box with its content.
6. **Add File as Prompt** Variable: If your prompt contains variables (e.g., {{fileName}}), right-click a file in the directory tree and select "Load as content for [variable_key]" to populate that variable with the file's content.
6. Optionally:
   - Enable or disable specific **rules**.
   - Add your **task description** in the input field.
   - Choose whether to **include the directory tree**.
5. Click **"Copy Context"**.
6. Or use **"Go To"** to copy the context and open ChatGPT or Claude directly in your browser.
8. **Paste the result into your LLM tool** to get results.

---

## 🗂 Interface Overview

| Area                   | Description                                                                                      |
|------------------------|--------------------------------------------------------------------------------------------------|
| **Directory Tree**     | Browse the file system. Drag files into the Context Buffer. Filter using regex if needed.       |
| **File Preview**       | Double-click any file to preview its contents. Select and right-click to add a snippet.         |
| **Context Buffer**     | Shows selected files and snippets to be included in the context. Supports drag & drop.          |
| **User Request Box**   | Optional field to describe the bug, feature request, or prompt to the LLM.                      |
| **Rules Selection**    | Check rules you'd like to include. Click ⚙️ to edit or create rules.                             |
| **Context Buffer Actions** | Use the buttons at the top-right of the buffer to delete items or copy the context. |

---

## ✅ Best Practices for Effective Context Creation

### 1. **Comprehensive Codebase Representation**

- ✅ **Include File Structure**  
  Keep "Include Tree Context" checked to provide the LLM with a visual summary of your directory hierarchy.

- ✅ **Drag Critical Files**  
  Add core classes, modules, or config files relevant to your task. This allows the LLM to reason with the actual logic in your system.

- ✅ **Select Key Snippets**  
  Use the preview pane to extract and include only the essential methods or blocks when full files are too large or noisy.

---

### 2. **Clear Instructions and Goals**

- ✅ **Fill in the "Describe your need..." box**  
  Write a clear task description. Specify the desired output, format, or coding constraints.

- ✅ **Break down complex tasks**  
  For multifaceted requests, explain them step-by-step in the user input. Example:
  > "First, create a function to parse the YAML config. Then integrate it into the CLI entry point."

---

### 3. **Use Rules for Focused Guidance**

- ✅ **Check Applicable Rules**  
  Include coding conventions, formatting preferences, or project-specific rules to guide LLM behavior.

- ⚙️ Click the gear icon → "Edit Rules" to add or update your rules.

---


## 💡 Tips & Tricks

- 🔍 **Regex file filter**: Use the input above the tree to filter visible files. Try `.*\.py$` to show only Python files.
- 🖱️ **Right-click power**: Right-click on tree items, file preview, or buffer items for advanced actions.
- ✏️ **Add as Prompt**: Use the tree view context menu to load a file's text directly into the prompt box.
- 📎 **Context is copied in plain text**: You can paste it directly into any chat with an LLM, or save it to a file for later use.
- 🧠 **LLM prompt hint**: Begin your prompt like this for better results:  
  > "Here's my code context for reference. Please help me [describe task]..."

---

## 🛠️ Troubleshooting

| Problem                                | Solution                                                                 |
|----------------------------------------|--------------------------------------------------------------------------|
| File preview not showing?              | Ensure it's a text-based file under the selected root directory.         |
| Rules not showing up?                  | Use the gear icon → Edit Rules → Save at least one rule.                 |
| Nothing copied after pressing "Copy"?  | Make sure you've added files/snippets and filled in the user request.    |

---

