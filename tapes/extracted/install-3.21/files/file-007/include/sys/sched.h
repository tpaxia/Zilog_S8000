/* @[$]sched.h	1.1  06/11/84 12:31:18 - Zilog Inc */
/* this is the new run queue, to balance run times accross process qroups */
/* the queue is an array of these structures--the 0th is the queue for procs */
/* with a priority of less than PUSER, and it's rq_nxt is the header of the */
/* frelist of rq entries (for when a new process group is created) */
struct rq{
	short rq_pgrp;		/* process group */
	unsigned int rq_cpu;	/* cpu ticks per process group */
	struct proc *rq_link;	/* list of processes ready to run */
	struct rq *rq_nxt;	/* next process group header (or next free) */
	struct rq *rq_prev;	/* previous process group header */
};
