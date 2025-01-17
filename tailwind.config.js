/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./se/blueprints/**/templates/**/*.html",
    "./se/blueprints/**/templates/*.html",
    "./se/templates/**/*.html",
    "./se/templates/*.html",

    "./se/blueprints/**/static/**/*.js",
    "./se/static/**/*.js",

    "./node_modules/flowbite/**/*.js",
  ],
  theme: {
    extend: {
      maxWidth: {
        '8xl': '90rem',
      },
    },
  },
  plugins: [
    require("flowbite/plugin"),
  ],
}

