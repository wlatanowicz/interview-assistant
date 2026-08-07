import {
  Button,
  Group,
  Modal,
  Select,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { translateApiError } from "../i18n/translateApiError";
import { createApplication } from "./api";
import {
  NON_TERMINAL_APPLICATION_STATES,
  type NonTerminalApplicationState,
} from "./types";

type NewApplicationModalProps = {
  opened: boolean;
  onClose: () => void;
  token: string;
  onCreated: () => void;
};

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export function NewApplicationModal({
  opened,
  onClose,
  token,
  onCreated,
}: NewApplicationModalProps) {
  const { t } = useTranslation();
  const [company, setCompany] = useState("");
  const [position, setPosition] = useState("");
  const [startedOn, setStartedOn] = useState(todayIsoDate());
  const [state, setState] = useState<NonTerminalApplicationState>("interested");
  const [adLink, setAdLink] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetForm = () => {
    setCompany("");
    setPosition("");
    setStartedOn(todayIsoDate());
    setState("interested");
    setAdLink("");
    setError(null);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    const result = await createApplication(token, {
      company,
      position,
      started_on: startedOn,
      state,
      ad_link: adLink.trim() || null,
    });
    setSubmitting(false);
    if (!result.ok) {
      setError(translateApiError(t, result.errorCode, result.errorParams));
      return;
    }
    resetForm();
    onCreated();
    onClose();
  };

  const stateOptions = NON_TERMINAL_APPLICATION_STATES.map((value) => ({
    value,
    label: t(`applications.states.${value}`),
  }));

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title={t("applications.newTitle")}
      centered
    >
      <Stack gap="sm">
        <TextInput
          label={t("applications.company")}
          value={company}
          onChange={(e) => setCompany(e.currentTarget.value)}
          required
        />
        <TextInput
          label={t("applications.position")}
          value={position}
          onChange={(e) => setPosition(e.currentTarget.value)}
          required
        />
        <TextInput
          label={t("applications.startedOn")}
          type="date"
          value={startedOn}
          onChange={(e) => setStartedOn(e.currentTarget.value)}
          required
        />
        <Select
          label={t("applications.state")}
          data={stateOptions}
          value={state}
          onChange={(value) => {
            if (value) {
              setState(value as NonTerminalApplicationState);
            }
          }}
          required
        />
        <TextInput
          label={t("applications.adLink")}
          value={adLink}
          onChange={(e) => setAdLink(e.currentTarget.value)}
          placeholder="https://"
        />
        {error ? (
          <Text c="red" size="sm">
            {error}
          </Text>
        ) : null}
        <Group justify="flex-end" mt="sm">
          <Button variant="default" onClick={handleClose} disabled={submitting}>
            {t("applications.cancel")}
          </Button>
          <Button
            onClick={() => void handleSubmit()}
            loading={submitting}
            disabled={!company.trim() || !position.trim() || !startedOn}
          >
            {t("applications.create")}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
