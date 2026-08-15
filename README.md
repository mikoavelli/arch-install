# Arch Linux Installation & Post-Configuration Scripts

An automated installation and post-configuration tool for setting up Arch Linux systems using a declarative `config.toml` specification.

Package selections, systemd service states, firewall rules, Secure Boot targets, locale configuration, and desktop settings are dynamically loaded from `config.toml`.

---

## Features

- **TOML-Based Setup**: Define custom package groups (`[packages.<group_name>]`), service states, firewall rules, system locales, and desktop defaults in `config.toml` (supports custom configs via `-c`/`--config`).
- **Dynamic Package Management**:
  - Automatically parses any custom package group key defined in `config.toml` (e.g., core, drivers, fonts, tools) and installs official repository packages automatically without prompting.
  - Reserved package group keys:
    - `aur`: Reserved for AUR packages via `yay` to apply specific build rules and flags (e.g., enabling PKGBUILD inspection).
    - `flatpak`: Reserved for Flathub packages.
  - Updates mirrorlists using `reflector` (can be skipped with `--skip-mirrors`) and synchronizes package databases.
  - Installs core packages and builds `yay` automatically if not present.
  - Supports version-locked package downgrades via `downgrade`.
  - Installs Flatpak applications from Flathub with environment, filesystem, and device overrides.
- **System Configuration**:
  - Configures incoming/outgoing UFW firewall rules.
  - Enables, disables, or masks systemd services and targets.
  - Configures `iwd` network management with `systemd-resolved`.
  - Generates system locales in `/etc/locale.gen` and configures localization settings in `/etc/locale.conf`.
  - Configures security parameters.
  - Configures Sudoers rules for hardware features.
  - Applies sysctl adjustments.
  - Silences PC speaker beeps and hides the systemd-boot menu.
- **Secure Boot**: Key generation, binary signing (`vmlinuz-linux`, `systemd-boot`, EFI files), and key enrollment via `sbctl`.
- **User Setup**:
  - SSH key creation (`github-sign`, `github-auth`) and SSH config generation.
  - Configures `allowed_signers` for SSH-based Git commit signing.
  - Applies interface theme and font preferences using `gsettings`.
- **Safety & Error Handling**:
  - Full support for `--dry-run` to preview commands without modifying the system.
  - Granular step control via `--step` and `--skip` flags.
  - Graceful error handling for missing/invalid configuration files and user cancellations (`Ctrl+C`, `EOF`) without raw Python tracebacks.
  - Root execution guard to prevent `yay` and `makepkg` build failures.

---

## Project Structure

```text
.
├── config.toml           # Configuration file for packages, services, and preferences
├── install.py            # Main installation script (system-level setup)
├── postinstall.py        # Post-installation script (SSH keys, Git config, GSettings, Rust)
├── installer/
│   ├── config.py         # TOML parsing logic and data models
│   ├── runner.py         # Subprocess execution helper with dry-run support
│   └── steps/
│       ├── bootstrap.py  # Reflector mirror update and pacman setup
│       ├── yay.py        # AUR helper installer
│       ├── packages.py   # Pacman, AUR, downgrade, and Flatpak installer
│       ├── system.py     # Systemd services, firewall, sysctl, faillock, network, locale, and hardware rules
│       └── secureboot.py # sbctl key generation and signing steps
├── pyproject.toml        # Development and linting configuration
└── .gitignore
```

---

## Requirements

- Arch Linux installation.
- Python 3.14 or higher.
- `sudo` privileges.

---

## Usage

### 1. Clone the Repository

```bash
git clone https://github.com/mikoavelli/arch-install.git
cd arch-install
```

### 2. Configure Settings

Review and edit `config.toml` to customize your installation:
- Adjust mirror countries under `[bootstrap]`.
- Define system locales and language settings under `[locale]`.
- Define any package groups under `[packages.<group_name>]` (e.g., `[packages.desktop]`, `[packages.fonts]`, `[packages.tools]`).
- Enable, disable, or mask systemd units in `[services]`.
- Define binaries to sign under `[secureboot]`.
- Adjust desktop settings under `[gschemas]`.

### 3. Run a Dry Run (Optional)

Preview the commands that will be run:

```bash
python3 install.py --dry-run
```

### 4. Run the Installer

Execute the primary script to perform system initialization, package installation, service configuration, and Secure Boot setup:

```bash
python3 install.py
```

#### Advanced Execution Options:

```bash
# Run only specific steps (bootstrap, yay, packages, system, secureboot)
python3 install.py --step packages,system

# Skip specific steps
python3 install.py --skip secureboot

# Use a custom config file
python3 install.py -c /path/to/custom_config.toml
```

### 5. Run Post-Installation Setup

Execute the post-installation script to generate SSH keys, configure Git signing, apply GSettings preferences, setup Rust:

```bash
python3 postinstall.py
```

*(Optionally pass `-c /path/to/custom_config.toml` to use a custom configuration file).*

### 6. Link Dotfiles

Link your configuration files (e.g., using GNU Stow from your dotfiles directory):

```bash
cd /path/to/dotfiles
stow .
```

---

## Configuration Reference (`config.toml`)

| Table | Description |
| :--- | :--- |
| `[bootstrap]` | Mirror country selection and base initialization packages. |
| `[packages.<group>]` | Custom package groups for official repo packages (installed automatically without prompts). Reserved keys: `aur` (applies custom AUR build rules/flags) and `flatpak` (installed via Flathub). |
| `[services]` | Lists of systemd units to enable, disable, or mask. |
| `[ufw]` | Port and protocol rules for the UFW firewall. |
| `[secureboot]` | Target binaries signed using `sbctl`. |
| `[locale]` | System language, regional formats, and localization generation settings. |
| `[git]` | Git configuration settings and placeholders. |
| `[gschemas]` | GSettings schema, key, and value entries. |

---

## Development

Static analysis and linting setup:

```bash
# Linting and formatting
uvx ruff check --fix
uvx ruff format

# Type checking
uvx basedpyright
```

---

## License

This project is open-source and released under the [GNU General Public License v3.0](LICENSE).