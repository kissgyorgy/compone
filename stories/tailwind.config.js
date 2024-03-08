/** @type {import('tailwindcss').Config} */

module.exports = {
  mode: "jit",
  content: ["./*/components.py"],
  theme: {
    minWidth: {
      "1/2": "50%",
    },
    extend: {},
  },
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/typography")],
};
