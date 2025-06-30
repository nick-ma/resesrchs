Great point — since modern macOS uses **zsh** (Z shell) as the default shell, it’s important to configure and, optionally, enhance it.

Here’s the **updated and complete guide**, now including **zsh setup and plugins**:

---

# 🍎 Mac Setup Guide for Data Science (with zsh, iTerm2, Conda, Git, and Homebrew)

### Covers:

1. Homebrew (package manager)
2. iTerm2 (modern terminal)
3. zsh (with optional plugin manager)
4. Git
5. Miniconda (Python env)
6. Python data science packages

---

## ✅ 0. Requirements

* macOS 10.13 or later
* Admin privileges (sudo access)
* Terminal or iTerm2

---

## 1. Install **Homebrew**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the instructions. Then:

For **Intel Macs**:

```bash
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/usr/local/bin/brew shellenv)"
```

For **Apple Silicon (M1/M2)**:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Check:

```bash
brew --version
```

---

## 2. Install **iTerm2**

```bash
brew install --cask iterm2
```

Or manually from [https://iterm2.com](https://iterm2.com).

---

## 3. Set Up & Enhance **zsh**

macOS uses `zsh` by default. You can enhance it with **Oh My Zsh** (plugin manager).

### Install Oh My Zsh

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

Once done, it creates `~/.zshrc` for configuration.

### (Optional) Install Powerlevel10k Theme

```bash
brew install romkatv/powerlevel10k/powerlevel10k
```

Then edit `~/.zshrc`:

```bash
ZSH_THEME="powerlevel10k/powerlevel10k"
```

Restart iTerm2 and follow the prompt.

### (Optional) Useful Plugins

Edit `~/.zshrc`:

```bash
plugins=(git z conda)
```

Then:

```bash
source ~/.zshrc
```

---

## 4. Install **Git**

Check:

```bash
git --version
```

If not present:

```bash
brew install git
```

Set identity:

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

## 5. Install **Miniconda**

### Step 1: Download Miniconda

Go to: [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)

Download for:

* `arm64` = Apple Silicon (M1/M2)
* `x86_64` = Intel

### Step 2: Run Installer

```bash
bash ~/Downloads/Miniconda3-latest-MacOSX-[arch].sh
```

Follow prompts. Agree to init shell when asked.

Then:

```bash
source ~/.zshrc
```

Check:

```bash
conda --version
```

---

## 6. Set Up Python Data Science Environment

### Create a New Conda Environment

```bash
conda create -n datasci python=3.10
conda activate datasci
```

### Install Core Packages

Using Conda:

```bash
conda install pandas numpy matplotlib seaborn scikit-learn jupyterlab
```

Optional:

```bash
conda install notebook ipykernel
```

Or use pip:

```bash
pip install pandas numpy matplotlib seaborn scikit-learn jupyterlab
```

---

## ✅ 7. Validate Setup

Open Python:

```bash
python
```

Paste this:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
```

If no errors — you're all set.

---

## 8. Launch **Jupyter Lab**

```bash
jupyter lab
```

Then open the browser it launches.

---

## 🧼 Final Tips

* Add `conda activate datasci` to `.zshrc` if you want it by default.
* Use `p10k configure` to reconfigure the zsh prompt anytime.
* Install `brew install htop tree` for handy terminal tools.

---

Let me know if you’d like a **shell script** version to automate this entire setup.
