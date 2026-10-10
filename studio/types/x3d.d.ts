import type * as React from "react";

declare module "react" {
  namespace JSX {
    interface IntrinsicElements {
      "x3d-canvas": React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement>,
        HTMLElement
      > & {
        src?: string;
        contentScale?: string;
        notifications?: string;
        splashScreen?: string;
      };
    }
  }
}
