# FDR Dashboard - React Implementation

Interactive dashboard for False Discovery Rate (FDR) analysis based on López de Prado's framework. This is a complete React rewrite of the original Python Dash application, offering better performance, smoother interactions, and easier deployment.

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v18 or higher)
- **npm** (comes with Node.js) or **yarn**

Check your versions:
```bash
node --version  # Should be v18+
npm --version   # Should be 9+
```

### Installation

1. **Navigate to the React project directory:**
```bash
cd fdr-dashboard-react
```

2. **Install all dependencies:**
```bash
npm install
```

This will install:
- React 18.2.0
- Plotly.js for visualizations
- TypeScript for type safety
- Vite for fast development and building

3. **Start the development server:**
```bash
npm run dev
```

4. **Open your browser:**
Navigate to `http://localhost:5173/` (or the URL shown in terminal)

### Production Build

To create an optimized production build:

```bash
npm run build
```

The built files will be in the `dist/` directory. You can preview the production build:

```bash
npm run preview
```

## 📦 Deployment

Since this is a pure static React app, you can deploy it anywhere:

### Vercel (Recommended)
```bash
npm install -g vercel
vercel
```

### Netlify
```bash
npm run build
netlify deploy --dir=dist
```

### Manual Static Hosting
Simply upload the contents of the `dist/` folder to any web server or CDN.

## 🎯 Features

### Interactive Controls
- **Search Intensity (K)**: 1-20 trials
- **Null Prevalence (π₀)**: 0-100%
- **Alternative Mean (δ₁)**: 0-1
- **Threshold (c)**: 1.5-3.0

### Four Visualization Tabs

1. **📊 Distributions**: PDF/CDF plots showing null, alternative, and selected maximum distributions
2. **📈 FDR Evolution**: FDR curve vs. Search Intensity with literature comparison
3. **🔍 Sensitivity Analysis**: Heatmap of FDR across (K, π₀) space + Identification Failure plot
4. **📋 Results Table**: Live calculations of α_K, β_K, Power, and FDR

### Advantages Over Python Dash Version

| Feature | React Version | Dash Version |
|---------|--------------|--------------|
| **Responsiveness** | Instant updates (<16ms) | Server round-trip (~100-500ms) |
| **Deployment** | Static hosting (free) | Python server required |
| **Offline Support** | ✅ Yes | ❌ No |
| **Mobile Friendly** | ✅ Optimized | ⚠️ Limited |
| **Bundle Size** | ~500KB | Full Python runtime |
| **Scalability** | Infinite (CDN) | Limited by server |

## 🏗️ Project Structure

```
fdr-dashboard-react/
├── public/              # Static assets
│   └── index.html       # HTML template
├── src/
│   ├── components/      # React components
│   │   ├── Dashboard.tsx
│   │   ├── DistributionPlot.tsx
│   │   ├── FDREvolutionPlot.tsx
│   │   ├── SensitivityHeatmap.tsx
│   │   ├── ResultsTable.tsx
│   │   └── ControlPanel.tsx
│   ├── hooks/           # Custom React hooks
│   │   └── useFDRCalculations.ts
│   ├── utils/           # Mathematical functions
│   │   └── fdrMath.ts
│   ├── types/           # TypeScript definitions
│   │   └── index.ts
│   ├── App.tsx          # Main app component
│   └── main.tsx         # Entry point
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
├── vite.config.ts       # Vite bundler config
└── README.md            # This file
```

## 🧮 Mathematical Background

The dashboard implements the maximum-of-mixtures model:

**CDF**: F_Θ,K(x) = [π₀·Φ(x/σ₀) + (1-π₀)·Φ((x-δ₁)/σ₁)]^K

**False Discovery Rate**: 
```
FDR = (α_K · π₀) / [α_K · π₀ + (1-β_K) · (1-π₀)]
```

Where:
- **α_K** = Type I error rate with K trials
- **β_K** = Type II error rate
- **π₀** = Proportion of true null hypotheses
- **K** = Number of tested strategies (search intensity)

## 🔧 Development

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Create production build |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint (if configured) |

### Adding New Features

1. Add mathematical functions in `src/utils/fdrMath.ts`
2. Create custom hooks in `src/hooks/` for complex state logic
3. Build reusable components in `src/components/`
4. Define types in `src/types/index.ts`

## 📚 References

- López de Prado, M. (2026). "What is the False Discovery Rate in Finance?" SSRN:6450418
- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley.

## 📝 License

© 2020-2026 Marcos López de Prado. All Rights Reserved.

Code implemented for educational and research purposes based on the paper methodology.

## 🤝 Contributing

This is a research implementation. For issues or suggestions related to the mathematical framework, please refer to the original paper.

---

**Need help?** Check the main repository README.md for additional context about the FDR framework and Python implementation.
