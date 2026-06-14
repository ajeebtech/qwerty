"use client";

import React, { useState, useRef, useEffect } from "react";

const ChevronDownIcon = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 16 16">
    <path d="M4 6L8 10L12 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const ChevronRightIcon = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 16 16">
    <path d="M6 12L10 8L6 4" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

// visitors.now-style logo (donut/circle shape)
const QwertyLogo = () => (
  <svg height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ flexShrink: 0 }}>
    <path
      d="M16 3C27 3 31 10 31 16C31 22 27 29 16 29C5 29 1 22 1 16C1 10 5 3 16 3ZM15 9C11.134 9 8 12.134 8 16C8 19.866 11.134 23 15 23H17C20.866 23 24 19.866 24 16C24 12.134 20.866 9 17 9H15Z"
      fill="currentColor"
    />
  </svg>
);

const TerminalIcon = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 16 16">
    <path d="M2 4l4 4-4 4M8 13h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const ServerIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 16 16">
    <path d="M2 4.5A1.5 1.5 0 013.5 3h9A1.5 1.5 0 0114 4.5v2A1.5 1.5 0 0112.5 8h-9A1.5 1.5 0 012 6.5v-2zM2 9.5A1.5 1.5 0 013.5 8h9A1.5 1.5 0 0114 9.5v2A1.5 1.5 0 0112.5 13h-9A1.5 1.5 0 012 11.5v-2z" stroke="currentColor" strokeWidth="1.5" />
    <circle cx="5" cy="5.5" r="0.75" fill="currentColor" />
    <circle cx="5" cy="10.5" r="0.75" fill="currentColor" />
  </svg>
);

const ShieldIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 16 16">
    <path d="M8 1.5L2 4v4c0 3.5 2.5 6.5 6 7.5 3.5-1 6-4 6-7.5V4L8 1.5z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    <path d="M5.5 8l1.5 1.5L10.5 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const LayersIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 16 16">
    <path d="M8 1.5l6 3-6 3-6-3 6-3zM2 8.5l6 3 6-3M2 11.5l6 3 6-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const BrainIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 16 16">
    <path d="M8 2c-1.5 0-2.8.8-3.5 2C2.5 4.3 1.5 5.7 1.5 7.5c0 1.3.6 2.4 1.5 3.1V12a.5.5 0 00.5.5h9a.5.5 0 00.5-.5v-1.4c.9-.7 1.5-1.8 1.5-3.1 0-1.8-1-3.2-2.5-3.5C11.8 2.8 10.5 2 8 2z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    <path d="M6 12.5V14M10 12.5V14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

const GlobeIcon = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 16 16">
    <path d="M8 15C11.866 15 15 11.866 15 8C15 4.13401 11.866 1 8 1M8 15C4.13401 15 1 11.866 1 8C1 4.13401 4.13401 1 8 1M8 15C6.22373 15 4.78378 11.866 4.78378 8C4.78378 4.13401 6.22373 1 8 1M8 15C9.77626 15 11.2162 11.866 11.2162 8C11.2162 4.13401 9.77626 1 8 1M14.8108 8H1.18919" stroke="currentColor" strokeWidth="1.25" strokeLinecap="square" />
  </svg>
);

const ArrowRightIcon = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 16 16">
    <path d="M9.17647 4L13 8L9.17647 12M3 8H12.1176" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const CheckCircleIcon = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 16 16">
    <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.5" />
    <path d="M5 8l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const SpeedIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 16 16">
    <path d="M10.2703 6.48649L8.19668 10.4609M14.0541 10.8378H1.94595M12.9497 3.05026C10.2161 0.316581 5.78393 0.316581 3.05026 3.05026C0.316581 5.78391 0.316581 10.2161 3.05026 12.9497C5.78391 15.6834 10.2161 15.6834 12.9497 12.9497C15.6834 10.2161 15.6834 5.78393 12.9497 3.05026Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const ClockIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 16 16">
    <path d="M8 4.78378V8L10.0811 10.0811M15 8C15 11.866 11.866 15 8 15C4.13401 15 1 11.866 1 8C1 4.13401 4.13401 1 8 1C11.866 1 15 4.13401 15 8Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const HeartIcon = () => (
  <svg width="20" fill="none" viewBox="0 0 17 16">
    <path d="M16 6.25C16 11.2813 9.12497 15 8.5 15C7.87503 15 1 11.2813 1 6.25C1 2.75 3.08333 1 5.16667 1C7.24997 1 8.5 2.3125 8.5 2.3125C8.5 2.3125 9.75003 1 11.8333 1C13.9167 1 16 2.75 16 6.25Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
  </svg>
);

// Referrer data for the mockup bar list
const REFERRER_DATA = [
  { label: "Google", gray: "50%", green: "50%", value: "2,341" },
  { label: "Direct", gray: "40%", green: "19%", value: "1,892" },
  { label: "GitHub", gray: "16%", green: "11%", value: "743" },
  { label: "Twitter", gray: "11%", green: null, value: "521" },
  { label: "Hacker News", gray: "9%", green: null, value: "412" },
  { label: "LinkedIn", gray: "6%", green: null, value: "298" },
];

// VPS Provider SVG Logos — real official paths, fill=currentColor for grayscale
const DigitalOceanLogo = () => (
  <svg height="26" viewBox="0 0 354 354" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-label="DigitalOcean">
    <path d="M177,221.5l0-34.2c36.2,0,64.3-35.9,50.4-74C222.3,99.3,211,88,196.9,82.9c-38.1-13.8-74,14.2-74,50.4l-34.1,0c0-57.7,55.8-102.7,116.3-83.8c26.4,8.3,47.5,29.3,55.7,55.7C279.7,165.7,234.7,221.5,177,221.5z"/>
    <polygon points="177.1,187.5 143,187.5 143,153.4 177.1,153.4"/>
    <polygon points="143,213.6 116.9,213.6 116.9,187.5 143,187.5"/>
    <path d="M116.9,187.5H95v-21.9h21.9V187.5z"/>
  </svg>
);

const HetznerLogo = () => (
  <svg height="16" viewBox="0 0 181.42 22.24" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-label="Hetzner">
    <path d="M174.05,14.12a10.22,10.22,0,0,0,4.53-2l0,0a6.15,6.15,0,0,0,1.68-4.78,7.71,7.71,0,0,0-1.14-4.06A6.47,6.47,0,0,0,173.84.09l-1.09,0L170.2,0,158.66,0c-.7,0-1,.29-1,1V21.22c0,.7.29,1,1,1h3c.7,0,1-.29,1-1v-6.7h3.67a3.48,3.48,0,0,1,2.17.91l5.82,5.85a3.08,3.08,0,0,0,2,.92h4.47c.7,0,.87-.41.38-.91Zm-.76-4.3H162.64V4.72h10.65a2.13,2.13,0,0,1,1.87,2.15v.79A2.14,2.14,0,0,1,173.29,9.82Z"/>
    <path d="M153,17.52H136.47V13.35h13.19c.7,0,1-.29,1-1V9.92c0-.7-.29-1-1-1h-13.2V4.76H153c.7,0,1-.29,1-1V1c0-.7-.29-1-1-1H132.38c-.7,0-1,.29-1,1V21.24c0,.7.29,1,1,1H153c.7,0,1-.29,1-1V18.51C154,17.81,153.67,17.52,153,17.52Z"/>
    <path d="M127.73,7.3a7.25,7.25,0,0,0-1.13-4A6.61,6.61,0,0,0,121.24,0L106.08,0c-.71,0-1,.29-1,1V21.22c0,.7.29,1,1,1h3.26c.7,0,1-.28,1-1V4.73l8.78,0c1.87,0,3.69,1.24,3.69,3.11V21.24c0,.7.29,1,1,1h2.95c.71,0,1-.29,1-1Z"/>
    <path d="M100.47,17.39l-14.25,0L100.5,4.84a2.57,2.57,0,0,0,1-1.84V1c0-.7-.3-1-1-1H79.83c-.7,0-1,.29-1,1V3.77c0,.7.29,1,1,1H93.08L79.79,17.24a2.62,2.62,0,0,0-1,1.84v2.17c0,.7.29,1,1,1l20.65,0c.7,0,1-.29,1-1V18.38C101.46,17.68,101.17,17.39,100.47,17.39Z"/>
    <path d="M74.19,0H53.55c-.71,0-1,.28-1,1V3.76c0,.7.28,1,1,1h7.78V21.24c0,.7.29,1,1,1h3.3c.7,0,1-.29,1-1V4.75h7.57c.7,0,1-.29,1-1V1C75.18.32,74.89,0,74.19,0Z"/>
    <path d="M47.91,17.52H31.41V13.35H44.6c.7,0,1-.29,1-1V9.92c0-.7-.28-1-1-1H31.41V4.76h16.5c.7,0,1-.29,1-1V1c0-.7-.29-1-1-1H27.33c-.7,0-1,.29-1,1V21.24c0,.7.29,1,1,1H47.91c.7,0,1-.29,1-1V18.51C48.9,17.81,48.61,17.52,47.91,17.52Z"/>
    <path d="M21.63,0H18.52c-.7,0-1,.29-1,1V8.87H5.13V1c0-.7-.29-1-1-1H1C.29,0,0,.29,0,1V21.25c0,.71.29,1,1,1H4.13c.7,0,1-.28,1-1v-8h12.4v8c0,.7.29,1,1,1h3.11c.7,0,1-.29,1-1V1C22.62.32,22.33,0,21.63,0Z"/>
  </svg>
);

const AWSLogo = () => (
  <svg height="26" viewBox="0 0 304 182" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-label="Amazon Web Services">
    <path d="M86.4,66.4c0,3.7,0.4,6.7,1.1,8.9c0.8,2.2,1.8,4.6,3.2,7.2c0.5,0.8,0.7,1.6,0.7,2.3c0,1-0.6,2-1.9,3l-6.3,4.2c-0.9,0.6-1.8,0.9-2.6,0.9c-1,0-2-0.5-3-1.4C76.2,90,75,88.4,74,86.8c-1-1.7-2-3.6-3.1-5.9c-7.8,9.2-17.6,13.8-29.4,13.8c-8.4,0-15.1-2.4-20-7.2c-4.9-4.8-7.4-11.2-7.4-19.2c0-8.5,3-15.4,9.1-20.6c6.1-5.2,14.2-7.8,24.5-7.8c3.4,0,6.9,0.3,10.6,0.8c3.7,0.5,7.5,1.3,11.5,2.2v-7.3c0-7.6-1.6-12.9-4.7-16c-3.2-3.1-8.6-4.6-16.3-4.6c-3.5,0-7.1,0.4-10.8,1.3c-3.7,0.9-7.3,2-10.8,3.4c-1.6,0.7-2.8,1.1-3.5,1.3c-0.7,0.2-1.2,0.3-1.6,0.3c-1.4,0-2.1-1-2.1-3.1v-4.9c0-1.6,0.2-2.8,0.7-3.5c0.5-0.7,1.4-1.4,2.8-2.1c3.5-1.8,7.7-3.3,12.6-4.5c4.9-1.3,10.1-1.9,15.6-1.9c11.9,0,20.6,2.7,26.2,8.1c5.5,5.4,8.3,13.6,8.3,24.6V66.4z M45.8,81.6c3.3,0,6.7-0.6,10.3-1.8c3.6-1.2,6.8-3.4,9.5-6.4c1.6-1.9,2.8-4,3.4-6.4c0.6-2.4,1-5.3,1-8.7v-4.2c-2.9-0.7-6-1.3-9.2-1.7c-3.2-0.4-6.3-0.6-9.4-0.6c-6.7,0-11.6,1.3-14.9,4c-3.3,2.7-4.9,6.5-4.9,11.5c0,4.7,1.2,8.2,3.7,10.6C37.7,80.4,41.2,81.6,45.8,81.6z M126.1,92.4c-1.8,0-3-0.3-3.8-1c-0.8-0.6-1.5-2-2.1-3.9L96.7,10.2c-0.6-2-0.9-3.3-0.9-4c0-1.6,0.8-2.5,2.4-2.5h9.8c1.9,0,3.2,0.3,3.9,1c0.8,0.6,1.4,2,2,3.9l16.8,66.2l15.6-66.2c0.5-2,1.1-3.3,1.9-3.9c0.8-0.6,2.2-1,4-1h8c1.9,0,3.2,0.3,4,1c0.8,0.6,1.5,2,1.9,3.9l15.8,67.1l17.3-67.1c0.6-2,1.3-3.3,2-3.9c0.8-0.6,2.1-1,3.9-1h9.3c1.6,0,2.5,0.8,2.5,2.5c0,0.5-0.1,1-0.2,1.6c-0.1,0.6-0.4,1.4-0.8,2.5l-24.1,77.3c-0.6,2-1.3,3.3-2.1,3.9c-0.8,0.6-2.1,1-3.8,1h-8.6c-1.9,0-3.2-0.3-4-1c-0.8-0.7-1.5-2-1.9-4l-15.5-64.7l-15.4,64.6c-0.5,2-1.1,3.3-1.9,4c-0.8,0.7-2.2,1-4,1H126.1z M242.5,95.3c-5.2,0-10.4-0.6-15.4-1.8c-5-1.2-8.9-2.5-11.5-4c-1.6-0.9-2.7-1.9-3.1-2.8c-0.4-0.9-0.6-1.9-0.6-2.8v-5.1c0-2.1,0.8-3.1,2.3-3.1c0.6,0,1.2,0.1,1.8,0.3c0.6,0.2,1.5,0.6,2.5,1c3.4,1.5,7.1,2.7,11,3.5c4,0.8,7.9,1.2,11.9,1.2c6.3,0,11.2-1.1,14.6-3.3c3.4-2.2,5.2-5.4,5.2-9.5c0-2.8-0.9-5.1-2.7-7c-1.8-1.9-5.2-3.6-10.1-5.2l-14.5-4.5c-7.3-2.3-12.7-5.7-16-10.2c-3.3-4.4-5-9.3-5-14.5c0-4.2,0.9-7.9,2.7-11.1c1.8-3.2,4.2-6,7.2-8.2c3-2.3,6.4-4,10.4-5.2c4-1.2,8.2-1.7,12.6-1.7c2.2,0,4.5,0.1,6.7,0.4c2.3,0.3,4.4,0.7,6.5,1.1c2,0.5,3.9,1,5.7,1.6c1.8,0.6,3.2,1.2,4.2,1.8c1.4,0.8,2.4,1.6,3,2.5c0.6,0.8,0.9,1.9,0.9,3.3v4.7c0,2.1-0.8,3.2-2.3,3.2c-0.8,0-2.1-0.4-3.8-1.2c-5.7-2.6-12.1-3.9-19.2-3.9c-5.7,0-10.2,0.9-13.3,2.8c-3.1,1.9-4.7,4.8-4.7,8.9c0,2.8,1,5.2,3,7.1c2,1.9,5.7,3.8,11,5.5l14.2,4.5c7.2,2.3,12.4,5.5,15.5,9.6c3.1,4.1,4.6,8.8,4.6,14c0,4.3-0.9,8.2-2.6,11.6c-1.8,3.4-4.2,6.4-7.4,8.8c-3.2,2.5-7,4.3-11.4,5.6C252.7,94.7,247.8,95.3,242.5,95.3z"/>
    <path d="M273.5,143.7c-32.9,24.3-80.7,37.2-121.8,37.2c-57.6,0-109.5-21.3-148.7-56.7c-3.1-2.8-0.3-6.6,3.4-4.4c42.4,24.6,94.7,39.5,148.8,39.5c36.5,0,76.6-7.6,113.5-23.2C274.2,133.6,278.9,139.7,273.5,143.7z"/>
    <path d="M287.2,128.1c-4.2-5.4-27.8-2.6-38.5-1.3c-3.2,0.4-3.7-2.4-0.8-4.5c18.8-13.2,49.7-9.4,53.3-5c3.6,4.5-1,35.4-18.6,50.2c-2.7,2.3-5.3,1.1-4.1-1.9C282.5,155.7,291.4,133.5,287.2,128.1z"/>
  </svg>
);

const HostingerLogo = () => (
  <svg height="18" viewBox="0 0 150 30" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-label="Hostinger">
    <path d="M0.000249566 14.046V0.000497794L7.08916 3.78046V10.1086L16.4735 10.1132L23.6774 14.046H0.000249566ZM18.3925 8.95058V0L25.6725 3.6859V13.1797L18.3925 8.95058ZM18.3924 26.1177V19.8441L8.93577 19.8375C8.9446 19.8793 1.6123 15.8418 1.6123 15.8418L25.6725 15.9547V30L18.3924 26.1177ZM0 26.1177L0.000252212 16.9393L7.08916 21.0683V29.8033L0 26.1177Z"/>
    <path d="M45.1114 8.89822H47.9253V21.3612H45.1114V16.0739H40.3857V21.3612H37.5718V8.89822H40.3857V13.6637H45.1114V8.89822Z"/>
    <path d="M54.4949 15.1209C54.4949 15.732 54.5698 16.2835 54.7201 16.7752C54.8704 17.267 55.0871 17.6895 55.3698 18.0431C55.6518 18.3972 55.9978 18.6695 56.4069 18.8612C56.8155 19.0535 57.2843 19.1496 57.8137 19.1496C58.3305 19.1496 58.7966 19.0535 59.2117 18.8612C59.6261 18.6695 59.9752 18.3972 60.2574 18.0431C60.5399 17.6895 60.7568 17.267 60.9071 16.7752C61.0574 16.2835 61.1326 15.732 61.1326 15.1209C61.1326 14.5091 61.0574 13.9546 60.9071 13.4569C60.7568 12.9595 60.5399 12.5342 60.2574 12.1802C59.9752 11.8266 59.6261 11.5535 59.2117 11.3621C58.7966 11.1702 58.3305 11.0744 57.8137 11.0744C57.2843 11.0744 56.8155 11.1732 56.4069 11.3709C55.9978 11.5688 55.6518 11.8447 55.3698 12.1985C55.0871 12.5521 54.8704 12.9776 54.7201 13.475C54.5698 13.9729 54.4949 14.5214 54.4949 15.1209ZM64.0369 15.1209C64.0369 16.1877 63.8773 17.1262 63.5593 17.935C63.2402 18.7445 62.8041 19.4219 62.2513 19.9672C61.6982 20.5131 61.0397 20.9235 60.2762 21.1991C59.5128 21.4753 58.6918 21.6131 57.8144 21.6131C56.9604 21.6131 56.1551 21.4753 55.3974 21.1991C54.6398 20.9235 53.9782 20.5131 53.4133 19.9672C52.8478 19.4219 52.4034 18.7445 52.0786 17.935C51.754 17.1262 51.5913 16.1877 51.5913 15.1209C51.5913 14.0537 51.7598 13.1154 52.0965 12.3064C52.4329 11.4969 52.8872 10.8164 53.4584 10.2649C54.0292 9.71341 54.6907 9.29998 55.4426 9.02411C56.1937 8.74799 56.9846 8.60993 57.8144 8.60993C58.6679 8.60993 59.4734 8.74799 60.2313 9.02411C60.9887 9.29998 61.65 9.71341 62.2152 10.2649C62.7802 10.8164 63.2253 11.4969 63.5499 12.3064C63.8748 13.1154 64.0369 14.0537 64.0369 15.1209Z"/>
    <path d="M88.4327 8.89829V11.2903H84.6629V21.3613H81.8492V11.2903H78.0792V8.89829H88.4327Z"/>
    <path d="M71.1123 19.2212C71.5091 19.2212 71.8367 19.1885 72.0952 19.1221C72.3537 19.0565 72.5613 18.9667 72.7174 18.852C72.8735 18.7386 72.982 18.6038 73.0423 18.4479C73.1025 18.2922 73.1326 18.1182 73.1326 17.9263C73.1326 17.5189 72.9399 17.1797 72.5552 16.9104C72.1704 16.6403 71.5091 16.3498 70.5713 16.0375C70.1623 15.8942 69.7534 15.7289 69.3446 15.5433C68.9358 15.3578 68.569 15.1239 68.2444 14.842C67.9201 14.5603 67.6553 14.2186 67.451 13.8164C67.2464 13.4151 67.1443 12.9267 67.1443 12.3511C67.1443 11.7755 67.2525 11.2569 67.4689 10.7954C67.6855 10.3337 67.992 9.94143 68.389 9.61728C68.7857 9.29338 69.2664 9.04517 69.8316 8.87089C70.3968 8.69737 71.0339 8.60986 71.7436 8.60986C72.5853 8.60986 73.3129 8.70039 73.9263 8.87995C74.5391 9.05975 75.0443 9.25792 75.441 9.47368L74.6297 11.6857C74.2806 11.5059 73.8927 11.3469 73.4662 11.2089C73.0392 11.0713 72.5252 11.0019 71.9242 11.0019C71.2506 11.0019 70.7666 11.0955 70.472 11.2811C70.1774 11.4669 70.0298 11.7518 70.0298 12.1351C70.0298 12.3632 70.0843 12.5553 70.1925 12.7107C70.3005 12.8666 70.4541 13.0074 70.6523 13.1334C70.8508 13.2592 71.0793 13.3733 71.3381 13.4749C71.5961 13.577 71.8818 13.6817 72.1948 13.7895C72.8438 14.0297 73.409 14.2663 73.8902 14.5002C74.3709 14.7341 74.7709 15.0069 75.0897 15.3185C75.408 15.6301 75.6456 15.996 75.8022 16.4157C75.9581 16.8357 76.0365 17.3449 76.0365 17.9439C76.0365 19.107 75.6274 20.0093 74.8098 20.6506C73.9921 21.2924 72.7595 21.6133 71.1123 21.6133C70.5592 21.6133 70.0601 21.5801 69.6152 21.5142C69.1703 21.4478 68.7766 21.3671 68.4339 21.2712C68.0913 21.1754 67.7965 21.0736 67.5498 20.9657C67.3034 20.8576 67.0961 20.756 66.9276 20.6597L67.7216 18.4298C68.0939 18.634 68.5539 18.8166 69.1015 18.978C69.6483 19.1402 70.3189 19.2212 71.1123 19.2212Z"/>
    <path d="M91.5579 21.3616H94.3718V8.89834H91.5579V21.3616Z"/>
    <path d="M106.967 21.3613C106.162 19.9347 105.29 18.5261 104.352 17.135C103.414 15.744 102.416 14.4313 101.358 13.1963V21.3613H98.58V8.89832H100.871C101.267 9.29364 101.706 9.77925 102.187 10.3549C102.668 10.9305 103.158 11.5451 103.657 12.1985C104.156 12.8518 104.652 13.5293 105.145 14.2304C105.638 14.9318 106.101 15.606 106.534 16.2535V8.89832H109.33V21.3613H106.967Z"/>
    <path d="M119.634 11.0564C118.324 11.0564 117.376 11.419 116.793 12.1443C116.21 12.8698 115.919 13.8616 115.919 15.121C115.919 15.7319 115.99 16.2869 116.135 16.7843C116.279 17.2815 116.496 17.71 116.784 18.0699C117.073 18.4297 117.433 18.7086 117.866 18.9065C118.299 19.1042 118.804 19.203 119.381 19.203C119.694 19.203 119.962 19.197 120.184 19.1852C120.406 19.1733 120.602 19.1495 120.77 19.1132V14.7793H123.584V20.9478C123.247 21.0798 122.706 21.2204 121.961 21.37C121.215 21.5196 120.295 21.5951 119.201 21.5951C118.263 21.5951 117.412 21.451 116.649 21.1635C115.885 20.8753 115.233 20.4561 114.692 19.9044C114.151 19.3531 113.733 18.6754 113.438 17.8722C113.143 17.0695 112.996 16.1521 112.996 15.121C112.996 14.0777 113.159 13.1545 113.484 12.351C113.808 11.548 114.252 10.867 114.818 10.3098C115.383 9.75224 116.047 9.32976 116.811 9.04207C117.575 8.75413 118.389 8.60978 119.255 8.60978C119.844 8.60978 120.376 8.64926 120.851 8.72697C121.326 8.80518 121.735 8.89496 122.078 8.99706C122.421 9.09865 122.703 9.20352 122.926 9.31165C123.148 9.41954 123.307 9.50378 123.404 9.56364L122.592 11.8113C122.207 11.6076 121.765 11.4311 121.266 11.281C120.767 11.1311 120.223 11.0564 119.634 11.0564Z"/>
    <path d="M127.521 21.3613V8.89832H135.963V11.2542H130.335V13.6998H135.331V16.0021H130.335V19.0055H136.378V21.3613H127.521Z"/>
    <path d="M143.596 11.1462C143.392 11.1462 143.209 11.1522 143.046 11.164C142.884 11.1764 142.731 11.1884 142.586 11.2V14.5809H143.38C144.438 14.5809 145.195 14.4496 145.652 14.1855C146.109 13.9223 146.337 13.4724 146.337 12.8366C146.337 12.225 146.106 11.791 145.643 11.5325C145.18 11.2752 144.498 11.1462 143.596 11.1462ZM143.435 8.75414C145.311 8.75414 146.748 9.08659 147.746 9.75225C148.744 10.4177 149.243 11.4517 149.243 12.8547C149.243 13.7296 149.042 14.4405 148.639 14.986C148.236 15.5312 147.656 15.9602 146.898 16.2716C147.151 16.5836 147.415 16.9402 147.692 17.3418C147.968 17.7437 148.242 18.1634 148.513 18.601C148.783 19.0386 149.045 19.494 149.297 19.9673C149.549 20.4413 149.784 20.9058 150 21.3612H146.855C146.625 20.9536 146.393 20.5401 146.158 20.1204C145.922 19.701 145.681 19.2931 145.434 18.8972C145.187 18.5014 144.941 18.1272 144.701 17.7736C144.459 17.4195 144.217 17.0989 143.976 16.8107H142.587V21.3612H139.774V9.07754C140.387 8.95834 141.021 8.87384 141.676 8.82631C142.332 8.77803 142.918 8.75414 143.435 8.75414Z"/>
  </svg>
);

const VPS_PROVIDERS = [
  { name: "DigitalOcean", Logo: DigitalOceanLogo, href: "https://digitalocean.com" },
  { name: "Hetzner",      Logo: HetznerLogo,      href: "https://hetzner.com" },
  { name: "AWS",          Logo: AWSLogo,           href: "https://aws.amazon.com" },
  { name: "Hostinger",    Logo: HostingerLogo,     href: "https://hostinger.com" },
];

export default function LandingPage({ onEnterConsole }) {
  const [activeTab, setActiveTab] = useState("Dashboard");
  const [cookieDismissed, setCookieDismissed] = useState(false);
  const [cliInput, setCliInput] = useState("");
  const [cliHistory, setCliHistory] = useState([
    { type: "output", text: "Welcome to qwerty AI VPS Manager. Type 'help' to get started." }
  ]);
  const cliBodyRef = useRef(null);

  const handleCliSubmit = (e) => {
    e.preventDefault();
    if (!cliInput.trim()) return;

    const cmd = cliInput.trim().toLowerCase();
    const newHistory = [...cliHistory, { type: "prompt", text: `$ ${cliInput}` }];

    setTimeout(() => {
      let response;
      if (cmd === "help") {
        response = "Available commands:\n  vps list         — List registered server connections\n  vps check memory — Ask the AI agent to inspect server RAM\n  vps init         — Configure a new system connection\n  vps snapshot     — Take a system snapshot\n  clear            — Clear the terminal";
      } else if (cmd === "vps list") {
        response = "Registered Server Profiles:\n  ● dev-vps          [127.0.0.1:2222]   — active\n  ● staging-server   [192.168.1.45:22]  — active\n  ○ prod-db-replica  [10.0.4.12:22]     — offline";
      } else if (cmd === "vps check memory") {
        response = "→ Asking Claude for plan...\n→ Running: free -h on dev-vps\n\n           total    used    free\nMem:       3.8Gi   1.2Gi   1.1Gi\n\n✓ VPS has healthy available RAM (2.3Gi free). No action needed.";
      } else if (cmd === "vps init") {
        response = "Initializing qwerty config...\n✓ Created config base at ~/.qwerty\n✓ Initialized SQLite storage: data.db\n\nRun 'vps list' to verify connections.";
      } else if (cmd === "vps snapshot") {
        response = "→ Taking snapshot of dev-vps...\n✓ CPU: 12% load average\n✓ RAM: 1.2Gi / 3.8Gi used\n✓ Disk: 18Gi / 80Gi used\n✓ Snapshot saved: snap_20260614_192455";
      } else if (cmd === "clear") {
        setCliHistory([]);
        setCliInput("");
        return;
      } else {
        response = `qwerty: command not found: '${cliInput}'\nTry 'help' for available commands.`;
      }
      setCliHistory([...newHistory, { type: "output", text: response }]);
    }, 200);

    setCliHistory(newHistory);
    setCliInput("");
  };

  useEffect(() => {
    if (cliBodyRef.current) {
      cliBodyRef.current.scrollTop = cliBodyRef.current.scrollHeight;
    }
  }, [cliHistory]);

  const tabs = ["Dashboard", "Logs", "Memory", "Snapshots", "Settings"];

  return (
    <div className="landing-root">
      {/* ── Floating Pill Header ── */}
      <header className="landing-header">
        <div className="landing-header-inner">
          {/* Logo */}
          <a className="landing-logo" onClick={onEnterConsole} style={{ cursor: "pointer" }}>
            <QwertyLogo />
          </a>

          {/* Nav links */}
          <nav className="landing-nav">
            <button className="landing-nav-link" type="button">
              Features <ChevronDownIcon />
            </button>
            <a href="#" className="landing-nav-link">Pricing</a>
            <a href="#" className="landing-nav-link">Blog</a>
            <a href="#" className="landing-nav-link">Docs</a>
          </nav>

          {/* Actions */}
          <div className="landing-header-actions">
            <a href="#" className="landing-login-link" onClick={onEnterConsole}>Login</a>
            <button className="btn-register" onClick={onEnterConsole}>Register</button>
          </div>
        </div>
      </header>

      {/* ── Hero Section ── */}
      <section className="landing-hero">
        <div className="hero-content">
          {/* Announcement badge */}
          <a className="announcement-badge" onClick={onEnterConsole} style={{ cursor: "pointer" }}>
            <span className="announcement-tag">new</span>
            <span style={{ position: "relative", display: "inline-block" }}>
              We hit v0.2.0 release
            </span>
            <ChevronRightIcon />
          </a>

          {/* Headline */}
          <h1 className="hero-title">
            Autonomous AI<br />VPS manager
          </h1>

          {/* Subtitle */}
          <p className="hero-subtitle">
            See every session in realtime and audit connection snapshots the moment they occur. Run dry-run commands and teach system memories in simple language.
          </p>

          {/* CTA Buttons */}
          <div className="hero-actions">
            <button className="btn-primary" onClick={onEnterConsole}>
              Launch console dashboard
            </button>
            <button className="btn-secondary" onClick={onEnterConsole}>
              See demo
            </button>
          </div>
        </div>

        {/* VPS Provider logos */}
        <div className="brand-logos-row">
          <p style={{ textAlign: "center", fontSize: "0.72rem", fontWeight: 600, color: "var(--fg-2)", marginBottom: "20px", letterSpacing: "0.08em", textTransform: "uppercase" }}>
            Works with any SSH-accessible server
          </p>
          <div className="brand-logos-inner">
            {VPS_PROVIDERS.map((provider) => (
              <div
                key={provider.name}
                className="brand-logo-item"
                title={provider.name}
              >
                <provider.Logo />
              </div>
            ))}
          </div>
        </div>

        {/* App Preview - gradient background section */}
        <div className="app-preview-section" style={{ marginTop: 0 }}>
          {/* Floating tab bar with corner cutouts */}
          <div className="app-preview-tab-container">
            <div className="app-preview-tabs">
              {tabs.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  className={`app-preview-tab ${activeTab === tab ? "active" : ""}`}
                  onClick={() => {
                    setActiveTab(tab);
                    if (tab !== "Dashboard") onEnterConsole();
                  }}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          {/* Terminal mockup */}
          <div className="app-preview-img-wrapper" style={{ paddingTop: "20px" }}>
            <div className="app-preview-terminal">
              {/* Terminal bar */}
              <div className="cli-bar">
                <div className="cli-dots">
                  <span className="cli-dot red" />
                  <span className="cli-dot yellow" />
                  <span className="cli-dot green" />
                </div>
                <div className="cli-title">qwerty@dev-vps — bash</div>
                <div style={{ width: 60 }} />
              </div>

              {/* Terminal body */}
              <div className="cli-body" ref={cliBodyRef}>
                {cliHistory.map((line, i) => (
                  <div
                    key={i}
                    className={`cli-line ${line.type === "prompt" ? "cli-prompt" : ""}`}
                    style={{ whiteSpace: "pre-wrap" }}
                  >
                    {line.text}
                  </div>
                ))}
                <form onSubmit={handleCliSubmit} className="cli-input-form">
                  <span className="cli-prompt-symbol">$</span>
                  <input
                    type="text"
                    className="cli-input-field"
                    value={cliInput}
                    onChange={(e) => setCliInput(e.target.value)}
                    placeholder="vps list"
                    autoFocus
                  />
                </form>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Feature showcase ── */}
      <div className="features-heading-section">
        <div className="features-heading-wrapper">
          <span className="features-badge">Features</span>
          <h2 className="features-heading">
            Everything you need to manage your servers
          </h2>
          <p className="features-subheading">
            From realtime command execution to AI memory, get the full picture of what's happening on your VPS.
          </p>
        </div>
      </div>

      {/* Feature Cards Grid */}
      <div className="feature-cards-grid">
        {/* Card 1 - Logs */}
        <div className="feature-card">
          <div className="feature-card-content">
            <span className="feature-icon-wrap" style={{ color: "var(--green-4)" }}>
              <TerminalIcon />
            </span>
            <h3 className="feature-card-title" style={{ color: "var(--green-4)" }}>
              Interactive logs
              <br />
              <span>Review every command, output, and exit code in realtime.</span>
            </h3>
            <ul className="feature-card-list">
              <li>
                <CheckCircleIcon style={{ color: "var(--green-4)", flexShrink: 0 }} />
                Logs update in real-time
              </li>
              <li>
                <CheckCircleIcon style={{ color: "var(--green-4)", flexShrink: 0 }} />
                Color-coded exit codes
              </li>
              <li>
                <CheckCircleIcon style={{ color: "var(--green-4)", flexShrink: 0 }} />
                Per-server filtering
              </li>
            </ul>
            <button className="feature-card-learn-more" onClick={onEnterConsole}>
              Open console <ChevronRightIcon />
            </button>
          </div>
          {/* Bar list mockup */}
          <div className="feature-card-visual" style={{ padding: "0 32px 24px" }}>
            {REFERRER_DATA.map((item) => (
              <div className="bar-list-item" key={item.label}>
                <div className="bar-track">
                  {item.green ? (
                    <>
                      <div className="bar-fill-gray" style={{ width: item.gray }} />
                      <div className="bar-fill-green" style={{ width: item.green }} />
                    </>
                  ) : (
                    <div className="bar-fill-only" style={{ width: item.gray }} />
                  )}
                </div>
                <div className="bar-list-inner">
                  <span style={{ color: "var(--fg-2)", flexShrink: 0 }}>
                    <GlobeIcon />
                  </span>
                  <span className="bar-list-label">{item.label}</span>
                  <span className="bar-list-value">{item.value}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Card 2 - AI Memory */}
        <div className="feature-card">
          <div className="feature-card-content">
            <span className="feature-icon-wrap" style={{ color: "var(--sky-4)" }}>
              <BrainIcon />
            </span>
            <div>
              <h3 className="feature-card-title" style={{ color: "var(--sky-4)" }}>
                AI memory
              </h3>
              <p className="feature-card-title" style={{ color: "var(--fg-4)", fontSize: "1.25rem" }}>
                Teach the agent your server config once and it never forgets.
              </p>
            </div>
            <ul className="feature-card-list">
              <li>
                <CheckCircleIcon style={{ color: "var(--sky-4)", flexShrink: 0 }} />
                Persistent knowledge DB
              </li>
              <li>
                <CheckCircleIcon style={{ color: "var(--sky-4)", flexShrink: 0 }} />
                Cross-session context
              </li>
              <li>
                <CheckCircleIcon style={{ color: "var(--sky-4)", flexShrink: 0 }} />
                User + AI inferred entries
              </li>
            </ul>
            <button className="feature-card-learn-more" onClick={onEnterConsole}>
              Open memory <ChevronRightIcon />
            </button>
          </div>
          {/* Memory count pill */}
          <div className="feature-card-visual" style={{ display: "flex", alignItems: "flex-end", justifyContent: "center", paddingBottom: "24px" }}>
            <div style={{
              background: "#0f172a",
              borderRadius: "9999px",
              padding: "8px 20px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              boxShadow: "0 4px 20px rgba(0,0,0,0.12)",
            }}>
              <BrainIcon style={{ color: "var(--purple-4)" }} />
              <span style={{
                fontSize: "1.125rem",
                fontWeight: "600",
                color: "#7c3aed",
                fontFamily: "var(--font-mono)",
                tabularNums: true,
              }}>12 memories</span>
            </div>
          </div>
        </div>

        {/* Card 3 - Snapshot Diffs */}
        <div className="feature-card">
          <div className="feature-card-content">
            <span className="feature-icon-wrap" style={{ color: "var(--pink-4)" }}>
              <LayersIcon />
            </span>
            <div>
              <h3 className="feature-card-title" style={{ color: "var(--pink-4)" }}>
                Snapshot diffs
              </h3>
              <p className="feature-card-title" style={{ color: "var(--fg-4)", fontSize: "1.25rem" }}>
                Compare system state over time. Spot config drift instantly.
              </p>
            </div>
            <ul className="feature-card-list">
              <li>
                <CheckCircleIcon style={{ color: "var(--pink-4)", flexShrink: 0 }} />
                CPU, RAM, disk, network
              </li>
              <li>
                <CheckCircleIcon style={{ color: "var(--pink-4)", flexShrink: 0 }} />
                Point-in-time comparison
              </li>
              <li>
                <CheckCircleIcon style={{ color: "var(--pink-4)", flexShrink: 0 }} />
                Stealth resource leak detection
              </li>
            </ul>
            <button className="feature-card-learn-more" onClick={onEnterConsole}>
              View snapshots <ChevronRightIcon />
            </button>
          </div>
          <div className="feature-card-visual" style={{ padding: "0 32px 24px" }}>
            {/* Mini diff mockup */}
            {[
              { label: "RAM", before: "1.2Gi", after: "2.8Gi", change: "+1.6Gi", warn: true },
              { label: "CPU", before: "12%", after: "18%", change: "+6%", warn: false },
              { label: "Disk", before: "18Gi", after: "22Gi", change: "+4Gi", warn: false },
            ].map((row) => (
              <div key={row.label} style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "10px 0",
                borderBottom: "1px solid var(--bg-a2)",
                fontSize: "0.875rem",
              }}>
                <span style={{ color: "var(--fg-2)", width: "40px" }}>{row.label}</span>
                <span style={{ color: "var(--fg-3)", fontFamily: "var(--font-mono)", fontSize: "0.8125rem" }}>{row.before}</span>
                <span style={{ color: "var(--fg-2)" }}>→</span>
                <span style={{ color: "var(--fg-4)", fontFamily: "var(--font-mono)", fontSize: "0.8125rem" }}>{row.after}</span>
                <span style={{
                  marginLeft: "auto",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.75rem",
                  color: row.warn ? "#ef4444" : "var(--fg-3)",
                  background: row.warn ? "rgba(239,68,68,0.08)" : "var(--bg-a1)",
                  padding: "2px 8px",
                  borderRadius: "9999px",
                  fontWeight: 600,
                }}>{row.change}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Card 4 - Safe Dry Runs */}
        <div className="feature-card">
          <div className="feature-card-content">
            <span className="feature-icon-wrap" style={{ color: "var(--purple-4)" }}>
              <ShieldIcon />
            </span>
            <div>
              <h3 className="feature-card-title" style={{ color: "var(--purple-4)" }}>
                Safe dry runs
              </h3>
              <p className="feature-card-title" style={{ color: "var(--fg-4)", fontSize: "1.25rem" }}>
                Every AI-generated command plan requires explicit confirmation.
              </p>
            </div>
            <ul className="feature-card-list">
              <li>
                <CheckCircleIcon style={{ color: "var(--purple-4)", flexShrink: 0 }} />
                Pre-execution review
              </li>
              <li>
                <CheckCircleIcon style={{ color: "var(--purple-4)", flexShrink: 0 }} />
                Rollback capability
              </li>
              <li>
                <CheckCircleIcon style={{ color: "var(--purple-4)", flexShrink: 0 }} />
                Audit trail for every run
              </li>
            </ul>
            <button className="feature-card-learn-more" onClick={onEnterConsole}>
              Learn more <ChevronRightIcon />
            </button>
          </div>
          <div className="feature-card-visual" style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "0 32px 24px" }}>
            {/* Dry run confirm mockup */}
            <div style={{
              background: "var(--bg-a1)",
              borderRadius: "12px",
              padding: "16px 20px",
              width: "100%",
              maxWidth: "320px",
            }}>
              <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--fg-2)", letterSpacing: "0.05em", textTransform: "uppercase", marginBottom: "10px" }}>
                Pending dry run
              </div>
              {["sudo apt update", "sudo apt upgrade -y", "systemctl restart nginx"].map((cmd, i) => (
                <div key={i} style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "6px 0",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.8125rem",
                  color: "var(--fg-4)",
                  borderBottom: i < 2 ? "1px solid var(--bg-a2)" : "none",
                }}>
                  <span style={{ color: "var(--purple-4)", fontSize: "0.75rem" }}>$</span>
                  {cmd}
                </div>
              ))}
              <div style={{ display: "flex", gap: "8px", marginTop: "12px" }}>
                <button style={{
                  flex: 1,
                  background: "var(--purple-4)",
                  color: "#fff",
                  border: "none",
                  borderRadius: "9999px",
                  padding: "6px 0",
                  fontSize: "0.8125rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  fontFamily: "var(--font-body)",
                }}>Approve</button>
                <button style={{
                  flex: 1,
                  background: "var(--bg-a2)",
                  color: "var(--fg-3)",
                  border: "none",
                  borderRadius: "9999px",
                  padding: "6px 0",
                  fontSize: "0.8125rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  fontFamily: "var(--font-body)",
                }}>Cancel</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── 3-column feature highlights ── */}
      <section className="showcase-section">
        <div className="showcase-item">
          <div className="showcase-icon-wrap" style={{ color: "var(--purple-4)" }}>
            <SpeedIcon />
          </div>
          <h3>
            Lightweight agent.{" "}
            <span>Single Python package. Connects in seconds. No bloated config.</span>
          </h3>
        </div>
        <div className="showcase-item">
          <div className="showcase-icon-wrap" style={{ color: "var(--purple-4)" }}>
            <ClockIcon />
          </div>
          <h3>
            5-minute setup.{" "}
            <span>One pip install. Add your server SSH keys and you're live.</span>
          </h3>
        </div>
        <div className="showcase-item">
          <div className="showcase-icon-wrap" style={{ color: "var(--purple-4)" }}>
            <HeartIcon />
          </div>
          <h3>
            Independent.{" "}
            <span>No VC funding. We ship what users ask for, not what investors want.</span>
          </h3>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <div className="footer-logo">qwerty.</div>
            <p className="footer-desc">Autonomous AI VPS manager.<br/>Deploy, monitor, and scale with natural language.</p>
          </div>
          <div className="footer-links-grid">
            <div className="footer-column">
              <h4>Product</h4>
              <a href="#">CLI</a>
              <a href="#">Console</a>
              <a href="#">Pricing</a>
              <a href="#">Changelog</a>
            </div>
            <div className="footer-column">
              <h4>Resources</h4>
              <a href="#">Documentation</a>
              <a href="#">API Reference</a>
              <a href="#">GitHub</a>
              <a href="#">Discord</a>
            </div>
            <div className="footer-column">
              <h4>Legal</h4>
              <a href="#">Privacy Policy</a>
              <a href="#">Terms of Service</a>
              <a href="#">Cookie Policy</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <span>© 2026 qwerty AI, Inc. All rights reserved.</span>
          <div className="footer-socials">
            <a href="#" aria-label="Twitter">Twitter</a>
            <a href="#" aria-label="GitHub">GitHub</a>
          </div>
        </div>
      </footer>

      {/* ── Cookie consent pill ── */}
      {!cookieDismissed && (
        <div className="cookie-pill">
          <span>We use cookies for analytics. You can accept or decline.</span>
          <div className="cookie-pill-actions">
            <button className="btn-cookie-decline" onClick={() => setCookieDismissed(true)}>
              DECLINE
            </button>
            <button className="btn-cookie-accept" onClick={() => { setCookieDismissed(true); onEnterConsole(); }}>
              ACCEPT
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
