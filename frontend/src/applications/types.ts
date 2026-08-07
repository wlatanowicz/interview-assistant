export const APPLICATION_STATES = [
  "interested",
  "applied",
  "screening",
  "interviewing",
  "assessment",
  "offer",
  "accepted",
  "rejected",
  "withdrawn",
  "ghosted",
] as const;

export type ApplicationState = (typeof APPLICATION_STATES)[number];

export const NON_TERMINAL_APPLICATION_STATES = [
  "interested",
  "applied",
  "screening",
  "interviewing",
  "assessment",
  "offer",
] as const;

export type NonTerminalApplicationState = (typeof NON_TERMINAL_APPLICATION_STATES)[number];

export type JobApplication = {
  id: string;
  company: string;
  position: string;
  state: ApplicationState;
  started_on: string;
  finished_on: string | null;
  ad_link: string | null;
  created_at: string;
  updated_at: string;
};

export type JobApplicationListResponse = {
  applications: JobApplication[];
};

export type JobApplicationCreatePayload = {
  company: string;
  position: string;
  started_on: string;
  state?: NonTerminalApplicationState;
  ad_link?: string | null;
};
