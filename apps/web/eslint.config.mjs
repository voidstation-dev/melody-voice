import next from "eslint-config-next";

// VoidMelody web ESLint config.
// `react-hooks/set-state-in-effect` is downgraded to "warn" because the
// existing codebase uses intentional synchronous setState in mount effects
// (e.g. reading localStorage, detecting the Tauri runtime). These are
// legitimate one-time initialization patterns, not cascading-render bugs.
export default [
  ...next,
  {
    ignores: [".next/**", "out/**", "node_modules/**", "src-tauri/**"],
  },
  {
    rules: {
      "react-hooks/set-state-in-effect": "warn",
    },
  },
];