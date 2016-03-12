#
# $FreeBSD$
#

PROG=			bsdjudge
SRCS=			src/main.c
LDADD=			-lpthread
MAKEOBJDIR=
MAN=
CC=clang

BINDIR=			/usr/local/sbin
BINMODE=		0755
FILES=			etc/bsdjudge.conf
FILESDIR=		/usr/local/etc
FILESMODE=		0644
SCRIPTS=		etc/rc.d/bsdjudge
SCRIPTSDIR=		/usr/local/etc/rc.d
SCRIPTSMODE=	0755

.include <bsd.prog.mk>
