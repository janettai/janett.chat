# Publishing Janett to Homebrew

## Prerequisites

- Package published to PyPI
- GitHub repository for the Homebrew tap

---

## Step 1: Publish to PyPI

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Upload to PyPI (you'll need PyPI credentials)
twine upload dist/*
```

## Step 2: Get the SHA256 Hash

After publishing to PyPI, get the hash:

```bash
curl -sL https://files.pythonhosted.org/packages/source/j/janett/janett-0.2.0.tar.gz | shasum -a 256
```

Copy the hash output.

## Step 3: Create Homebrew Tap Repository

1. Create a new GitHub repository named `homebrew-janett` at:
   ```
   https://github.com/janettai/homebrew-janett
   ```

2. Create the directory structure:
   ```
   homebrew-janett/
   └── Formula/
       └── janett.rb
   ```

3. Copy `Formula/janett.rb` from this repo to the tap repo

4. Update the SHA256 hash in the formula:
   ```ruby
   sha256 "YOUR_ACTUAL_SHA256_HASH_HERE"
   ```

5. Commit and push

## Step 4: Test the Tap

```bash
# Tap your repository
brew tap janettai/janett

# Install
brew install janett

# Test
janett --version
```

## Step 5: Update README

Add to installation instructions:

```markdown
### Homebrew (macOS/Linux)

```bash
brew tap janettai/janett
brew install janett
```
```

---

## Updating the Formula

When releasing a new version:

1. Publish new version to PyPI
2. Get new SHA256: `curl -sL https://files.pythonhosted.org/packages/source/j/janett/janett-X.Y.Z.tar.gz | shasum -a 256`
3. Update `Formula/janett.rb`:
   - Change `url` version number
   - Change `sha256` hash
4. Commit and push to homebrew-janett repo

---

## Formula Reference

The formula is located at: `Formula/janett.rb`

```ruby
class Janett < Formula
  include Language::Python::Virtualenv

  desc "Interactive tutorial generator powered by local LLMs or OpenAI"
  homepage "https://github.com/janettai/janett.chat"
  url "https://files.pythonhosted.org/packages/source/j/janett/janett-0.2.0.tar.gz"
  sha256 "REPLACE_AFTER_PYPI_PUBLISH"
  license "MIT"
  head "https://github.com/janettai/janett.chat.git", branch: "main"

  depends_on "python@3.12"

  def install
    virtualenv_create(libexec, "python3.12")
    system libexec/"bin/pip", "install", "janett==#{version}"
    bin.install_symlink libexec/"bin/janett"
  end

  def caveats
    <<~EOS
      Janett works best with Ollama for free, local AI:

        brew install ollama
        ollama pull llama3.2
        ollama serve

      Then run: janett

      Or use OpenAI by setting your API key in the app with /apikey
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/janett --version 2>&1")
  end
end
```

---

## Alternative: pipx (No Tap Needed)

If you don't want to maintain a Homebrew tap, users can install via pipx:

```bash
brew install pipx
pipx install janett
```

This is simpler but requires users to have pipx installed.
