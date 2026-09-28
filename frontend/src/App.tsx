import { Alert, Badge, Button, Container, Group, Text, Title } from "@mantine/core";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { Dashboard } from "./applications/Dashboard";
import { AuthPanel } from "./auth/AuthPanel";
import { fetchAuthConfig, loadMe, parseOAuthHash } from "./auth/api";
import type { AuthConfig, MeUser } from "./auth/types";
import { LanguageSelector } from "./i18n/LanguageSelector";
import { translateApiError } from "./i18n/translateApiError";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const ACCESS_TOKEN_KEY = "access_token";

export function App() {
  const { t } = useTranslation();
  const [configError, setConfigError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<MeUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);
  const [bootstrapped, setBootstrapped] = useState(false);

  const getStoredToken = useCallback((): string | null => {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }, []);

  const clearSession = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    setCurrentUser(null);
    setAccessToken(null);
  }, []);

  const restoreSession = useCallback(
    async (token: string) => {
      const r = await loadMe(token);
      if (!r.ok) {
        if (r.status === 401 || r.status === 403) {
          clearSession();
        }
        return;
      }
      setAccessToken(token);
      setCurrentUser(r.data);
    },
    [clearSession],
  );

  useEffect(() => {
    if (!apiBaseUrl) {
      setConfigError(t("errors.apiBaseNotSet"));
      return;
    }

    void (async () => {
      try {
        const oauthResult = parseOAuthHash();
        if (oauthResult.authErrorCode) {
          setAuthError(translateApiError(t, oauthResult.authErrorCode));
        }

        const config = await fetchAuthConfig();
        if (config) {
          setAuthConfig(config);
        }

        const tkn = oauthResult.accessToken ?? getStoredToken();
        if (tkn) {
          if (oauthResult.accessToken) {
            localStorage.setItem(ACCESS_TOKEN_KEY, tkn);
          }
          await restoreSession(tkn);
        }
      } catch (e) {
        setConfigError(e instanceof Error ? e.message : t("errors.requestFailed"));
      } finally {
        setBootstrapped(true);
      }
    })();
  }, [getStoredToken, restoreSession, t]);

  const methods: AuthConfig = authConfig ?? {
    password: true,
    google: false,
    facebook: false,
  };

  return (
    <Container size="md" py="xl">
      <Group justify="space-between" align="flex-start" mb="md" wrap="wrap">
        <Title order={1}>{t("app.title")}</Title>
        <Group gap="xs" aria-live="polite">
          <LanguageSelector />
          {currentUser ? (
            <>
              <Text fw={600}>{currentUser.email}</Text>
              <Badge variant="light">{currentUser.status}</Badge>
              <Button
                variant="subtle"
                size="compact-sm"
                onClick={clearSession}
                disabled={false}
              >
                {t("app.signOut")}
              </Button>
            </>
          ) : (
            <Text c="dimmed" size="sm">
              {t("app.notSignedIn")}
            </Text>
          )}
        </Group>
      </Group>

      <Text c="dimmed" mb="lg">
        {t("app.subtitle")}
      </Text>

      {configError ? (
        <Alert color="red" title={t("errors.configuration")} mb="md">
          {configError}
        </Alert>
      ) : null}

      {!configError && bootstrapped && !currentUser ? (
        <AuthPanel
          authConfig={methods}
          initialError={authError}
          onSession={(user, token) => {
            setCurrentUser(user);
            setAccessToken(token);
            setAuthError(null);
          }}
        />
      ) : null}

      {!configError && currentUser && accessToken ? (
        <Dashboard token={accessToken} />
      ) : null}
    </Container>
  );
}
