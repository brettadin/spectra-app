# Differential workspace reference

Use the differential tab to quantify how two spectra differ once they are
aligned to the same wavelength sampling.

## Workflow

1. **Choose Trace A and Trace B.** Traces list in the same order as the overlay
   table. By default the current reference trace is pre-selected.
2. **Pick an operation.**
   - *Subtract (A − B)* highlights residual flux after removing Trace B from
     Trace A.
   - *Ratio (A ÷ B)* reveals multiplicative differences. A tiny epsilon is added
     to the denominator to keep the division numerically stable.
3. **Set the sample density.** The resampler projects both traces onto a shared
   grid between their overlapping wavelength bounds. Higher sample counts
   provide smoother curves but take longer to compute.
4. **Run the computation.** The result is cached in the session so you can tweak
   options without recomputing immediately.

## Reading the output

- The **stacked plot** shows the aligned source spectra on top and the derived
  differential curve underneath. Both panels share the x-axis, making it easy to
  connect residual features with original lines.
- The **summary table** lists min/max/mean statistics for Trace A, Trace B, and
  the result. It also records the effective wavelength range and number of
  samples used.

When a result is useful, click **Add to overlays** to push it into the main
workspace. Differential overlays inherit metadata that lists the source traces
and operation so you can keep track of how they were produced.
