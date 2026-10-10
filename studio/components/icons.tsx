import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function IconBase({ children, ...props }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {children}
    </svg>
  );
}

export const CubeIcon = (props: IconProps) => (
  <IconBase {...props}>
    <path d="m12 2.7 8 4.5v9.2l-8 4.9-8-4.9V7.2l8-4.5Z" />
    <path d="m4.4 7.4 7.6 4.5 7.6-4.5M12 21v-9.1" />
  </IconBase>
);

export const ChatIcon = (props: IconProps) => (
  <IconBase {...props}>
    <path d="M20 15a3 3 0 0 1-3 3H9l-5 3v-6a3 3 0 0 1-1-2.2V7a3 3 0 0 1 3-3h11a3 3 0 0 1 3 3v8Z" />
    <path d="M8 9h8M8 13h5" />
  </IconBase>
);

export const EyeIcon = (props: IconProps) => (
  <IconBase {...props}>
    <path d="M2.5 12s3.4-6 9.5-6 9.5 6 9.5 6-3.4 6-9.5 6-9.5-6-9.5-6Z" />
    <circle cx="12" cy="12" r="2.5" />
  </IconBase>
);

export const InspectorIcon = (props: IconProps) => (
  <IconBase {...props}>
    <path d="M5 3.5h14a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2Z" />
    <path d="M8 8h8M8 12h8M8 16h5" />
  </IconBase>
);

export const SparkIcon = (props: IconProps) => (
  <IconBase {...props}>
    <path d="m12 2 1.25 4.75L18 8l-4.75 1.25L12 14l-1.25-4.75L6 8l4.75-1.25L12 2Z" />
    <path d="m19 14 .7 2.3L22 17l-2.3.7L19 20l-.7-2.3L16 17l2.3-.7L19 14Z" />
  </IconBase>
);

export const SendIcon = (props: IconProps) => (
  <IconBase {...props}>
    <path d="m21 3-7.4 18-3.2-7.4L3 10.4 21 3Z" />
    <path d="m10.4 13.6 4.3-4.3" />
  </IconBase>
);

export const DownloadIcon = (props: IconProps) => (
  <IconBase {...props}>
    <path d="M12 3v12m0 0 4-4m-4 4-4-4M4 20h16" />
  </IconBase>
);

export const RotateIcon = (props: IconProps) => (
  <IconBase {...props}>
    <path d="M20 7v5h-5" />
    <path d="M19 12a7 7 0 1 1-2-5l3 3" />
  </IconBase>
);

export const CheckIcon = (props: IconProps) => (
  <IconBase {...props}>
    <path d="m5 12 4 4 10-10" />
  </IconBase>
);

export const CopyIcon = (props: IconProps) => (
  <IconBase {...props}>
    <rect x="8" y="8" width="11" height="11" rx="2" />
    <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" />
  </IconBase>
);

export const TerminalIcon = (props: IconProps) => (
  <IconBase {...props}>
    <path d="m5 7 4 4-4 4M11 16h8" />
  </IconBase>
);

export const AlertIcon = (props: IconProps) => (
  <IconBase {...props}>
    <path d="M12 3 2.8 20h18.4L12 3Z" />
    <path d="M12 9v4m0 3h.01" />
  </IconBase>
);
