SRCS = $(wildcard *.asy)
PROGS = $(patsubst %.asy,%,$(SRCS))
all: $(PROGS)
%: %.asy
	asy -render 5 -f png $<
