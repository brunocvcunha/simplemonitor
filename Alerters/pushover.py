# coding=utf-8
import requests

from .alerter import Alerter


class PushoverAlerter(Alerter):
    """Send push notification via Pushover."""

    def __init__(self, config_options):
        Alerter.__init__(self, config_options)

        self.pushover_token = Alerter.get_config_option(
            config_options,
            'token',
            required=True,
            allow_empty=False
        )
        self.pushover_user = Alerter.get_config_option(
            config_options,
            'user',
            required=True,
            allow_empty=False
        )

        self.support_catchup = True

    def send_pushover_notification(self, subject, body):
        """Send a push notification."""

        requests.post('api.pushover.net:443/1/messages.json',
                      data={
                          "token": self.pushover_token,
                          "user": self.pushover_user,
                          "title": subject,
                          "message": body,
                      })

    def send_alert(self, name, monitor):
        """Build up the content for the push notification."""

        type = self.should_alert(monitor)
        (days, hours, minutes, seconds) = self.get_downtime(monitor)

        if monitor.is_remote():
            host = " on %s " % monitor.running_on
        else:
            host = " on host %s" % self.hostname

        subject = ""
        body = ""

        if type == "":
            return
        elif type == "failure":
            subject = "[%s] Monitor %s Failed!" % (self.hostname, name)
            body = """Monitor %s%s has failed.\n
            Failed at: %s
            Downtime: %d+%02d:%02d:%02d
            Virtual failure count: %d
            Additional info: %s
            Description: %s""" % (
                name,
                host,
                self.format_datetime(monitor.first_failure_time()),
                days, hours, minutes, seconds,
                monitor.virtual_fail_count(),
                monitor.get_result(),
                monitor.describe())
            try:
                if monitor.recover_info != "":
                    body += "\nRecovery info: %s" % monitor.recover_info
            except AttributeError:
                body += "\nNo recovery info available"

        elif type == "success":
            subject = "[%s] Monitor %s succeeded" % (self.hostname, name)
            body = "Monitor %s%s is back up.\nOriginally failed at: %s\nDowntime: %d+%02d:%02d:%02d\nDescription: %s" % (name, host, self.format_datetime(monitor.first_failure_time()), days, hours, minutes, seconds, monitor.describe())

        elif type == "catchup":
            subject = "[%s] Monitor %s failed earlier!" % (self.from_addr, self.to_addr, self.hostname, name)
            body = "Monitor %s%s failed earlier while this alerter was out of hours.\nFailed at: %s\nVirtual failure count: %d\nAdditional info: %s\nDescription: %s" % (name, host, self.format_datetime(monitor.first_failure_time()), monitor.virtual_fail_count(), monitor.get_result(), monitor.describe())

        else:
            print("Unknown alert type %s" % type)
            return

        if not self.dry_run:
            try:
                self.send_pushover_notification(subject, body)
            except Exception as e:
                print("Couldn't send push notification: %s", e)
                self.available = False
        else:
            print("dry_run: would send push notification: %s" % body)
