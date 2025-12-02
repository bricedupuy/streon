# Contributing to Streon

Thank you for your interest in contributing to Streon!

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/streon.git
   cd streon
   ```

2. **Set up the backend**
   ```bash
   cd controller
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd web-ui
   npm install
   ```

4. **Run development servers**
   ```bash
   # Terminal 1 - Backend
   cd controller
   uvicorn main:app --reload

   # Terminal 2 - Frontend
   cd web-ui
   npm run dev
   ```

## Project Structure

- `controller/` - Python FastAPI backend
- `web-ui/` - React TypeScript frontend
- `liquidsoap/` - Liquidsoap script templates
- `services/` - Systemd service files
- `install/` - Installation scripts
- `docs/` - Documentation

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use meaningful variable names

### TypeScript/React

- Use TypeScript strict mode
- Follow React best practices
- Use functional components with hooks
- Prefer named exports

## Commit Messages

Follow conventional commits:

```
feat: add StereoTool preset upload
fix: resolve device scanning timeout
docs: update installation guide
refactor: simplify Flow manager
test: add device manager tests
```

## Pull Request Process

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Make your changes
3. Test thoroughly
4. Commit your changes (`git commit -m 'feat: add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Testing

```bash
# Backend tests (when available)
cd controller
pytest

# Frontend tests (when available)
cd web-ui
npm test
```

## Questions?

Feel free to open an issue for any questions or concerns.
