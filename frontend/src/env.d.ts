/// <reference types="vite/client" />

declare global {
  interface Window {
    // API based on https://umami.is/docs/tracker-functions
    umami: {
      /**
       * Tracks the current page
       */
      track(): void;

      /**
       * Custom payload
       */
      track(payload: object): void;

      /**
       * Custom event
       */
      track(event_name: string): void;

      /**
       * Custom event with data
       */
      track(event_name: string, data: object): void;

      /**
       * Assign ID to current session
       */
      identify(unique_id: string): void;

      /**
       * Session data
       */
      identify(unique_id: string, data: object): void;

      /**
       * Session data without ID
       */
      identify(data: object): void;
    };
  }
}


declare const window: Window;
export const window;
