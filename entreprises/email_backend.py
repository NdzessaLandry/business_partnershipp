import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend


class SSLEmailBackend(EmailBackend):

    def open(self):
        if self.connection:
            return False

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode    = ssl.CERT_NONE

        try:
            if self.use_ssl:
                # Port 465 — connexion SSL directe dès le départ
                self.connection = smtplib.SMTP_SSL(
                    self.host,
                    self.port,
                    timeout=self.timeout or 30,
                    context=context,
                )
            else:
                # Port 587 — STARTTLS après connexion
                self.connection = smtplib.SMTP(
                    self.host,
                    self.port,
                    timeout=self.timeout or 30,
                )
                self.connection.ehlo()
                if self.use_tls:
                    self.connection.starttls(context=context)
                    self.connection.ehlo()

            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True

        except Exception:
            if not self.fail_silently:
                raise