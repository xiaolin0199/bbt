#!/usr/bin/env python
# coding=utf-8
import gc
import inspect

gc.set_debug(
    gc.DEBUG_UNCOLLECTABLE |
    gc.DEBUG_INSTANCES |
    gc.DEBUG_OBJECTS |
    gc.DEBUG_SAVEALL
)


def show_leaks():
    gc.collect()
    del gc.garbage[:]
    gc.collect()

    print "%s GARBAGE OBJECTS" % len(gc.garbage)
    for x in gc.garbage:
        s = str(x)
        if len(s) > 74:
            s = "%s..." % s[:74]
        print "-> %s" % s
        print "   type: %s" % type(x)
        print "   refs: %d" % len(gc.get_referrers(x))
        try:
            print "   cls : %s" % inspect.isclass(type(x))
            print "   mod : %s" % inspect.getmodule(x)

            lines, line_num = inspect.getsourcelines(type(x))
            print "   code (%s)" % line_num
            i = 0
            for l in lines:
                print "       %d: %s" % (i, l.rstrip("\n"))
                i += 1
        except:
            pass

        print

    del gc.garbage[:]
