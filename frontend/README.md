# ECO PACK AI - Frontend

A beautiful, modern SaaS-level frontend for sustainable packaging recommendations.

## Features

✨ **Beautiful UI**
- Modern gradient design with smooth animations
- Responsive layout (mobile, tablet, desktop)
- Dark-aware color scheme optimized for sustainability

🎯 **Pages**
- **Dashboard** - Overview and quick start
- **Product Form** - Input product specifications
- **Recommendations** - AI-powered material suggestions with scoring
- **History** - Track all previous analyses

📊 **Components**
- Circular progress/score indicators
- Cards with hover effects
- Stat cards with trends
- Responsive navigation

## Tech Stack

- **React 18** - UI framework
- **Vite** - Fast build tool
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization (prepared)
- **Axios** - API calls (prepared)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

3. Build for production:
```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Navbar.jsx       - Navigation bar
│   │   ├── Card.jsx         - Reusable card component
│   │   ├── ScoreRing.jsx    - Circular score visualization
│   │   └── StatCard.jsx     - Statistics card
│   ├── pages/
│   │   ├── Dashboard.jsx    - Home page
│   │   ├── ProductForm.jsx  - Product input
│   │   ├── Recommendations.jsx - Material recommendations
│   │   └── History.jsx      - Analysis history
│   ├── App.jsx              - Main app component
│   ├── main.jsx             - Entry point
│   └── index.css            - Global styles
├── index.html
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── package.json
```

## API Integration

The frontend is configured to proxy API calls to `http://localhost:5000/api`.

Update the proxy settings in `vite.config.js` if needed.

## Features in Detail

### Dashboard
- Welcome hero section
- Key metrics (products analyzed, CO₂ reduction, etc.)
- Feature highlights
- Top eco-friendly materials

### Product Form
- Product name and category selection
- Weight input
- Interactive sliders for strength, biodegradability, recyclability
- Form validation
- Notes/description field

### Recommendations
- Product summary card
- 6 material options with eco scores
- Detailed analysis view with pros/cons
- Visual score rings (Overall, Recyclability, Carbon, Biodegradability)
- Material selection functionality

### History
- All analyzed products list
- Sort and filter options
- Quick preview cards
- Click to view detailed recommendations

## Customization

### Colors
Edit `tailwind.config.js` to change the color scheme:
```javascript
colors: {
  primary: '#10b981',      // Green
  secondary: '#059669',    // Dark green
  accent: '#f59e0b'        // Amber
}
```

### Animations
Animations are defined in `src/index.css`. Modify the keyframes for different effects.

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- Code splitting with Vite
- Lazy loading ready
- Optimized bundle size
- Fast hot module replacement (HMR)

## Future Enhancements

- [ ] Real API integration
- [ ] User authentication
- [ ] Dark mode toggle
- [ ] Export reports
- [ ] Advanced filtering
- [ ] API key management
- [ ] Cost comparison charts
- [ ] CO₂ impact calculator

## License

MIT
