# Inst4Brut3
Dictionary Style Attack, Test passwords from a common password list or you're own, if you need any help please be sure to let me know if you if you have any questions or concerns

Below is the Step by Step Guide 

Before you run your code there is couple things you need to do before running your code:

## 📂 Wordlist Requirement

This script requires a wordlist to function.

You will need to either:

* **Create your own wordlist** as a `.txt` file, or
* Obtain an existing wordlist such as `rockyou.txt`.

Place the wordlist inside your **Documents** folder. The script itself can be located and run from any directory.

### Example Setup

```text
Downloads/
└── your-script.py

Documents/
├── rockyou.txt
└── passlist.txt
```

### Selecting Your Wordlist

When the script runs, it will ask you to enter the **file** you want to use.

Enter **only the filename without the `.txt` extension**.

For example, if your wordlist is:

```text
Documents/passlist.txt
```

Enter:

```text
passlist
```

**Do NOT enter:**

```text
passlist.txt
```

Another example: for `rockyou.txt`, simply enter:

```text
rockyou
```

The script automatically looks inside the **Documents** folder and adds/handles the `.txt` filename format for you.

> Only use password-testing functionality on systems and accounts you own or have explicit permission to test.


# 🚀 How to Run

## 1. Clone the repository

git clone https://github.com/n0tc4isti4n/Inst4Brut3

## 2. Download All Python requirements 

python3 -m pip install selenium requests
python3 -m pip install requests

## 3. Give Permission to File 

chmod +x Inst4Brut3.py

## 4. Run The File

./Inst4Brut3.py

## ⚠️ Disclaimer

This project is provided for **educational, research, and authorized security testing purposes only**. It is intended for use on systems, websites, accounts, and environments that you personally own or have explicit permission to test.

By using this software, you agree that you are solely responsible for how it is used. Do not use this tool to gain unauthorized access to accounts, systems, networks, or data, or to perform any activity that violates applicable laws, regulations, or terms of service.

The developer does not encourage, support, or condone malicious or unethical use of this software and assumes no responsibility or liability for damage, data loss, account restrictions, legal consequences, or other issues resulting from misuse.

**Only test targets you own or have explicit authorization to test.**
