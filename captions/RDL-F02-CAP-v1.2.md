# RDL Figure F02 Caption v1.2

Artefact status: reproducible figure candidate; operator accepted.

**Two distinct clock mappings for meta-order delivery and impact.** Panel A,
“Calendar-time delivery of one event-time meta-order,” directly implements the
paper's inverse-counter subordination. It applies the right-continuous event
counter `N_t=max{m:T_m<=t}` to 256 positive child orders of size `1/256` and
plots normalized cumulative executed volume `Q_{N_t}/Q`. Calendar time is
normalized by the constant-clock completion time. The realized completion
ratios are 1.00 (constant), 0.99 (exponential), 0.73 (finite-mean Lomax) and
21.86 (infinite-mean Pareto-I). Each stochastic curve is one seeded
realization, not a distributional estimate; the Pareto-I law has no population
mean and its realized completion lies outside the displayed window.

Panel B, “Subordinated reduced Abel impact response,” is the supplementary
operational-time construction `I_B(t)=I_u(U(t))`, with deterministic activity
clock `U(t)=alpha_U t`. The three curves use `alpha_U=0.5,1,2`, giving
calendar-time completion at `t/T_u=2,1,0.5`, respectively. The three-unit
calendar horizon shows completion and post-completion relaxation for every
activity, while the native Abel response is valid through `u/T_u=6`.

The panels map different native objects: cumulative delivery in Route A and
reduced impact in Route B. The deterministic activity clocks in Panel B are not
the stochastic waiting-time paths in Panel A. The routes are not composed, no
pointwise correspondence between their curves is imposed, and no joint
stochastic coupling is claimed. The figure is a simulation-only illustration,
not an empirical calibration or a lattice/PDE simulation.
