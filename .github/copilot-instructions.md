# Copilot Instructions for skravleboks
## Project Goals
- Optimize all code for deployment and performance on Raspberry Pi (ARM architecture, limited resources).
- Ensure full compatibility and smooth development experience on MacOS.

## Coding Guidelines
- Prefer lightweight libraries and dependencies that run efficiently on Raspberry Pi.
- Avoid x86-specific code or dependencies; always check ARM compatibility.
- Use cross-platform APIs and avoid OS-specific features unless absolutely necessary.
- Test all scripts and binaries on both MacOS and Raspberry Pi.
- For performance-critical code, profile on Raspberry Pi and optimize for CPU/memory usage.

## Development Workflow
- Develop and test primarily on MacOS.
- Use Docker or emulation for Raspberry Pi when possible.
- Document any platform-specific setup or configuration steps.
- Provide clear instructions for deploying to Raspberry Pi.

## Compatibility
- All shell scripts must run in zsh (MacOS default) and bash (Raspberry Pi default).
- Python code should be compatible with Python 3.x on both platforms.
- Avoid Node.js unless necessary; if used, ensure it runs on ARM architecture.

## Testing
- Include tests for both MacOS and Raspberry Pi environments.
- Use CI/CD workflows that build and test on both platforms if possible.

## Documentation
- Clearly mark any code or instructions that are platform-specific.
- Provide troubleshooting tips for common Raspberry Pi issues (e.g., missing dependencies, low memory).