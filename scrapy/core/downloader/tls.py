import logging
from OpenSSL import SSL


logger = logging.getLogger(__name__)

METHOD_SSLv3 = 'SSLv3'
METHOD_TLS = 'TLS'
METHOD_TLSv10 = 'TLSv1.0'
METHOD_TLSv11 = 'TLSv1.1'
METHOD_TLSv12 = 'TLSv1.2'

openssl_methods = {
    METHOD_TLS:    SSL.SSLv23_METHOD,                   # protocol negotiation (recommended)
    METHOD_SSLv3:  SSL.SSLv3_METHOD,                    # SSL 3 (NOT recommended)
    METHOD_TLSv10: SSL.TLSv1_METHOD,                    # TLS 1.0 only
    METHOD_TLSv11: getattr(SSL, 'TLSv1_1_METHOD', 5),   # TLS 1.1 only
    METHOD_TLSv12: getattr(SSL, 'TLSv1_2_METHOD', 6),   # TLS 1.2 only
}

# ClientTLSOptions requires a recent-enough version of Twisted
try:

    # taken from twisted/twisted/internet/_sslverify.py
    try:
        from OpenSSL.SSL import SSL_CB_HANDSHAKE_DONE, SSL_CB_HANDSHAKE_START
    except ImportError:
        SSL_CB_HANDSHAKE_START = 0x10
        SSL_CB_HANDSHAKE_DONE = 0x20

    from twisted.internet._sslverify import (ClientTLSOptions,
                                             _maybeSetHostNameIndication,
                                             verifyHostname,
                                             VerificationError)

    class ScrapyClientTLSOptions(ClientTLSOptions):
        # same as Twisted's ClientTLSOptions,
        # except that VerificationError is caught
        # and doesn't close the connection
        def _identityVerifyingInfoCallback(self, connection, where, ret):
            if where & SSL_CB_HANDSHAKE_START:
                _maybeSetHostNameIndication(connection, self._hostnameBytes)
            elif where & SSL_CB_HANDSHAKE_DONE:
                try:
                    verifyHostname(connection, self._hostnameASCII)
                except VerificationError as e:
                    logger.warning(e)

except ImportError:
    # ImportError should not matter for older Twisted versions
    # as the above is not used in the fallback ScrapyClientContextFactory
    pass
