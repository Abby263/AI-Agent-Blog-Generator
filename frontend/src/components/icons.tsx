import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

const baseProps: IconProps = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
};

export function HomeIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5 10v9.5h14V10" />
      <path d="M10 19.5v-5.25h4V19.5" />
    </svg>
  );
}

export function DashboardIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.4" />
      <rect x="13.5" y="3.5" width="7" height="4" rx="1.4" />
      <rect x="13.5" y="10.5" width="7" height="10" rx="1.4" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1.4" />
    </svg>
  );
}

export function ComposeIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M5 19h14" />
      <path d="m13.5 5 5.5 5.5L9.5 20H4v-5.5z" />
      <path d="m11 7 6 6" />
    </svg>
  );
}

export function LibraryIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M5 4h4v16H5z" />
      <path d="M11 4h4v16h-4z" />
      <path d="m17 5.2 3.6 1 -3.4 14.6 -3.6 -1z" />
    </svg>
  );
}

export function ReviewIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M4 5.5C6.5 4 9.5 4 12 6c2.5-2 5.5-2 8 -.5v12c-2.5-1.5-5.5-1.5-8 .5-2.5-2-5.5-2-8-.5z" />
      <path d="M12 6v12" />
    </svg>
  );
}

export function MemoryIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <rect x="3.5" y="6" width="17" height="12" rx="2" />
      <path d="M7 6V4M11 6V4M17 6V4M7 20v-2M13 20v-2M17 20v-2" />
      <rect x="8" y="9.5" width="8" height="5" rx="1" />
    </svg>
  );
}

export function SettingsIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <circle cx="12" cy="12" r="2.5" />
      <path d="M19.5 12c0-.5-.05-1-.13-1.46l1.78-1.4-1.75-3.03-2.13.7a7.45 7.45 0 0 0-2.53-1.46L14.4 3h-4.8l-.34 2.35a7.45 7.45 0 0 0-2.53 1.46l-2.13-.7L2.85 9.14l1.78 1.4a7.5 7.5 0 0 0 0 2.92l-1.78 1.4 1.75 3.03 2.13-.7a7.45 7.45 0 0 0 2.53 1.46L9.6 21h4.8l.34-2.35a7.45 7.45 0 0 0 2.53-1.46l2.13.7 1.75-3.03-1.78-1.4c.08-.46.13-.96.13-1.46Z" />
    </svg>
  );
}

export function GithubIcon(props: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
      {...props}
    >
      <path
        clipRule="evenodd"
        d="M12 2C6.48 2 2 6.58 2 12.23c0 4.51 2.87 8.34 6.84 9.69.5.09.68-.22.68-.49 0-.24-.01-1.04-.01-1.89-2.78.62-3.37-1.22-3.37-1.22-.45-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.63.07-.63 1 .07 1.53 1.06 1.53 1.06.9 1.56 2.35 1.11 2.92.85.09-.66.35-1.11.64-1.37-2.22-.26-4.55-1.14-4.55-5.05 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.27 2.75 1.05A9.32 9.32 0 0 1 12 6.92c.85 0 1.71.12 2.51.35 1.91-1.32 2.75-1.05 2.75-1.05.55 1.41.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.92-2.34 4.78-4.57 5.04.36.32.68.94.68 1.9 0 1.37-.01 2.48-.01 2.81 0 .27.18.59.69.49A10.1 10.1 0 0 0 22 12.23C22 6.58 17.52 2 12 2Z"
        fillRule="evenodd"
      />
    </svg>
  );
}

export function ArrowRightIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M5 12h14" />
      <path d="m13 5 7 7-7 7" />
    </svg>
  );
}

export function CheckIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="m5 12.5 4.5 4.5L19 7" />
    </svg>
  );
}

export function CloseIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="m6 6 12 12M18 6 6 18" />
    </svg>
  );
}

export function RefreshIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M4 11a8 8 0 0 1 14-4.5L20 9" />
      <path d="M20 4v5h-5" />
      <path d="M20 13a8 8 0 0 1-14 4.5L4 15" />
      <path d="M4 20v-5h5" />
    </svg>
  );
}

export function SparkIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8" />
    </svg>
  );
}

export function BookOpenIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M3 5.5C5.5 4.5 8.5 4.5 12 6c3.5-1.5 6.5-1.5 9-.5v13c-2.5-1-5.5-1-9 .5-3.5-1.5-6.5-1.5-9-.5z" />
      <path d="M12 6v13" />
    </svg>
  );
}

export function FileTextIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
      <path d="M14 3v6h6" />
      <path d="M8 13h8M8 17h6M8 9h2" />
    </svg>
  );
}

export function FlaskIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M9 3h6" />
      <path d="M10 3v5L4.5 18A2 2 0 0 0 6.3 21h11.4a2 2 0 0 0 1.8-3L14 8V3" />
      <path d="M7.5 14h9" />
    </svg>
  );
}

export function GraphIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <circle cx="6" cy="6" r="2.5" />
      <circle cx="18" cy="6" r="2.5" />
      <circle cx="12" cy="18" r="2.5" />
      <path d="M7.7 7.7 10.5 16M16.3 7.7 13.5 16M8.5 6h7" />
    </svg>
  );
}

export function ServerIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <rect x="3.5" y="4" width="17" height="6" rx="1.5" />
      <rect x="3.5" y="14" width="17" height="6" rx="1.5" />
      <path d="M7 7h.01M7 17h.01" />
    </svg>
  );
}

export function MenuIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M4 7h16M4 12h16M4 17h16" />
    </svg>
  );
}
