/* @[$]pwd.h	2.1  07/23/82 17:36:08 - Zilog Inc */
struct	passwd {
	char	*pw_name;
	char	*pw_passwd;
	int	pw_uid;
	int	pw_gid;
	char	*pw_age;
	char	*pw_comment;
	char	*pw_gecos;
	char	*pw_dir;
	char	*pw_shell;
};
