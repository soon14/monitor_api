from email_util import conf
from logger_util import write_log
import smtplib
import os
from past.builtins import basestring
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate
try:
    from collections.abc import Iterable as CollectionIterable
except ImportError:
    from collections import Iterable as CollectionIterable


def send_email_smtp(to, subject, html_content, files=None, dryrun=False, cc=None, bcc=None, mime_subtype='mixed',
                    mime_charset='us-ascii', **kwargs):
    smtp_mail_from = conf.smtp_mail_from

    to = get_email_address_list(to)

    msg = MIMEMultipart(mime_subtype)
    msg['Subject'] = subject
    msg['From'] = smtp_mail_from
    msg['To'] = ", ".join(to)
    recipients = to
    if cc:
        cc = get_email_address_list(cc)
        msg['CC'] = ", ".join(cc)
        recipients = recipients + cc

    if bcc:
        # don't add bcc in header
        bcc = get_email_address_list(bcc)
        recipients = recipients + bcc

    msg['Date'] = formatdate(localtime=True)
    mime_text = MIMEText(html_content, 'html', mime_charset)
    msg.attach(mime_text)

    for fname in files or []:
        basename = os.path.basename(fname)
        with open(fname, "rb") as f:
            part = MIMEApplication(
                f.read(),
                Name=basename
            )
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename
            part['Content-ID'] = '<%s>' % basename
            msg.attach(part)

    send_MIME_email(smtp_mail_from, recipients, msg, dryrun)


def send_MIME_email(e_from, e_to, mime_msg, dryrun=False):

    SMTP_HOST = conf.smtp_host
    SMTP_PORT = conf.smtp_port
    SMTP_STARTTLS = conf.smtp_starttls
    SMTP_SSL = conf.smtp_ssl
    SMTP_USER = conf.smtp_user
    SMTP_PASSWORD = conf.smtp_password

    if not dryrun:
        s = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) if SMTP_SSL else smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        if SMTP_STARTTLS:
            s.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            s.login(SMTP_USER, SMTP_PASSWORD)
        s.sendmail(e_from, e_to, mime_msg.as_string())
        s.quit()


def get_email_address_list(addresses):
    if isinstance(addresses, basestring):
        return _get_email_list_from_str(addresses)

    elif isinstance(addresses, CollectionIterable):
        if not all(isinstance(item, basestring) for item in addresses):
            raise TypeError("The items in your iterable must be strings.")
        return list(addresses)

    received_type = type(addresses).__name__
    raise TypeError("Unexpected argument type: Received '{}'.".format(received_type))


def _get_email_list_from_str(addresses):
    delimiters = [",", ";"]
    for delimiter in delimiters:
        if delimiter in addresses:
            return [address.strip() for address in addresses.split(delimiter)]
    return [addresses]


def _send_email(to, subject, html_content, files=None, dryrun=False, cc=None, bcc=None, mime_subtype='mixed',
                mime_charset='us-ascii', **kwargs):

    to = get_email_address_list(to)
    to = ", ".join(to)

    return send_email_smtp(to, subject, html_content, files=files,
                   dryrun=dryrun, cc=cc, bcc=bcc,
                   mime_subtype=mime_subtype, mime_charset=mime_charset, **kwargs)


def send_eamil(to, subject, html_content, retry=1, files=None, dryrun=False, cc=None, bcc=None, mime_subtype='mixed',
               mime_charset='us-ascii', **kwargs):
    for i in range(retry):
        write_log('main', '发送邮件...')
        try:
            _send_email(to, subject, html_content, files=files, dryrun=dryrun, cc=cc, bcc=bcc,
                        mime_subtype=mime_subtype, mime_charset=mime_charset, **kwargs)
            write_log('main', '发送邮件成功')
            break
        except:
            write_log('main', '发送邮件失败 ==> ' + str(i+1) + ', 最多尝试 ==> ' + str(retry))
            pass


if __name__ == '__main__':
    to = []
    cc = []
    subject = ''
    html_content = ''
    mime_charset = 'utf8'
    _send_email(to, subject, html_content, cc=cc, mime_charset=mime_charset)
