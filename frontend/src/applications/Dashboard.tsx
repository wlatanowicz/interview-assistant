import {
  Alert,
  Badge,
  Button,
  Group,
  Loader,
  Paper,
  Stack,
  Table,
  Text,
  Title,
} from "@mantine/core";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { translateApiError } from "../i18n/translateApiError";
import { listApplications } from "./api";
import { NewApplicationModal } from "./NewApplicationModal";
import type { JobApplication } from "./types";

type DashboardProps = {
  token: string;
};

export function Dashboard({ token }: DashboardProps) {
  const { t } = useTranslation();
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const loadApplications = useCallback(async () => {
    setLoading(true);
    setError(null);
    const result = await listApplications(token, { active: true });
    setLoading(false);
    if (!result.ok) {
      setError(translateApiError(t, result.errorCode, result.errorParams));
      setApplications([]);
      return;
    }
    setApplications(result.data);
  }, [t, token]);

  useEffect(() => {
    void loadApplications();
  }, [loadApplications]);

  return (
    <>
      <Paper withBorder p="md" radius="md">
        <Group justify="space-between" mb="md" align="center">
          <Title order={2} size="h3">
            {t("dashboard.title")}
          </Title>
          <Button onClick={() => setModalOpen(true)}>{t("applications.new")}</Button>
        </Group>

        {error ? (
          <Alert color="red" title={t("errors.configuration")} mb="md">
            {error}
          </Alert>
        ) : null}

        {loading ? (
          <Group justify="center" py="xl">
            <Loader />
          </Group>
        ) : applications.length === 0 ? (
          <Stack align="center" gap="xs" py="xl">
            <Text c="dimmed">{t("dashboard.empty")}</Text>
            <Button variant="light" onClick={() => setModalOpen(true)}>
              {t("applications.new")}
            </Button>
          </Stack>
        ) : (
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>{t("applications.company")}</Table.Th>
                <Table.Th>{t("applications.position")}</Table.Th>
                <Table.Th>{t("applications.state")}</Table.Th>
                <Table.Th>{t("applications.startedOn")}</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {applications.map((application) => (
                <Table.Tr key={application.id}>
                  <Table.Td>{application.company}</Table.Td>
                  <Table.Td>{application.position}</Table.Td>
                  <Table.Td>
                    <Badge variant="light">
                      {t(`applications.states.${application.state}`)}
                    </Badge>
                  </Table.Td>
                  <Table.Td>{application.started_on}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Paper>

      <NewApplicationModal
        opened={modalOpen}
        onClose={() => setModalOpen(false)}
        token={token}
        onCreated={() => void loadApplications()}
      />
    </>
  );
}
