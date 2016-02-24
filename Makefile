#
# $FreeBSD$
#

PROG=		bsdjudge
SRCS=		src/main.c
MAKEOBJDIR=
MAN=

BINDIR=		/usr/local/sbin
BINMODE=	0755
FILESGROUPS=	CONF
CONF=		etc/judge.conf
CONFDIR=	/usr/local/etc
CONFMODE=	0644

.include <bsd.prog.mk>
