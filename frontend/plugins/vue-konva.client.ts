import { defineNuxtPlugin } from "#app";
import VueKonva from "vue-konva";

export default defineNuxtPlugin((nuxtApp) => {
  const app = nuxtApp.vueApp as typeof nuxtApp.vueApp & {
    __vueKonvaInstalled?: boolean;
  };

  if (import.meta.server) {
    return;
  }

  // In dev, Vite HMR can re-execute this plugin on the *same* app instance
  // (e.g. when this file itself is edited). Vue's app.use() warns if the
  // same plugin is installed twice on one app, so guard against re-running
  // the install (and re-wrapping the warnHandler below) more than once.
  if (app.__vueKonvaInstalled) return;
  app.__vueKonvaInstalled = true;

  app.use(VueKonva);

  // vue-konva's node components (v-group, v-rect, v-text, ...) don't draw
  // real DOM elements -- Konva paints everything on the <canvas> itself --
  // so internally they render as a fragment/comment placeholder rather than
  // a single root element. That's exactly the documented, correct way to
  // bind click/tap/dragend handlers to them (see konvajs.org/docs/vue/Events.html),
  // but it means Vue can't auto-inherit those listeners and logs a harmless
  // "Extraneous non-emits event listeners ... renders fragment or text root
  // nodes" warning on every click/tap/dragend. The handlers still fire
  // correctly either way; we just silence this one specific, known-noisy
  // warning so real warnings don't get lost in the console.
  const defaultWarnHandler = app.config.warnHandler;
  app.config.warnHandler = (msg, instance, trace) => {
    if (msg.includes("renders fragment or text root nodes")) return;
    if (defaultWarnHandler) {
      defaultWarnHandler(msg, instance, trace);
    } else {
      console.warn(msg, trace);
    }
  };
});
