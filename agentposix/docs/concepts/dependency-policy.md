# Dependency Management Policy

To ensure that Agent POSIX remains highly compatible with parent applications while keeping builds stable and reproducible, we implement a two-tiered dependency pinning strategy.

---

## 1. Runtime Dependencies

Runtime dependencies are the packages required to run Agent POSIX. These are declared in the `dependencies` array under the `[project]` section of `pyproject.toml`.

- **Strategy:** Loose semantic version ranges.
- **Rules:**
  - We do not use exact version pins (e.g. `==1.2.3`) for runtime dependencies, as this creates dependency conflicts for applications integrating our library.
  - We use loose bounds that restrict major updates that could introduce breaking changes, while allowing bug fixes and minor features (e.g. `click>=8.1,<9`).
  - Minimum versions must correspond to the oldest version that supports our required features and Python range.

---

## 2. Optional Integrations and Extras

Integrations with external frameworks (like LangGraph or SQLite backends) are declared under `[project.optional-dependencies]` in `pyproject.toml`.

- **Strategy:** Loose ranges or minimum bounds.
- **Rules:**
  - To prevent forcing optional packages on users who do not need them, we keep imports lazy.
  - We pin a minimum supported version (e.g. `langgraph>=0.2.62`) to ensure that users installing the `adapters` extra receive a version compatible with our mappings.

---

## 3. Development and Contributor Dependencies

Development dependencies are tools required for running tests, formatting, generating docs, and building the package. These are declared under the `dev` group in `[project.optional-dependencies]` in `pyproject.toml`.

- **Strategy:** Conservative, compatible pinning.
- **Rules:**
  - We pin minimum versions for dev tools (e.g., `pytest>=8.0.0`, `ruff>=0.15.2`) to ensure contributors have access to required options.
  - Periodic checks (e.g. quarterly) should be conducted to update dev tools to their latest major/minor releases.

---

## 4. Review and Upgrade Guidelines

- **Security Advisories:** If any vulnerability is reported in a runtime or development dependency (via tools like GitHub Dependabot or safety scans), we prioritize updating our bounds and publishing a patch release.
- **Expanding Python Matrix:** When new Python versions (e.g. Python 3.13) are released, we verify compatibility in dev environments and extend our `requires-python` or classifiers only after confirming all tests pass.
