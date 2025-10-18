**📊 ANOVA Results: Comparison of Patient vs. System Waiting Times**

| Source      | Df  | Sum Sq   | Mean Sq  | F value | Pr(>F)     | Significance |
|--------------|-----|----------|----------|----------|-------------|---------------|
| Source       | 1   | 9,219,795 | 9,219,795 | 75.08    | 6.79e-14    | ***           |
| Residuals    | 103 | 12,649,235 | 122,808 | —        | —           | —             |


Based on the comparisons of simulated data and the average wait time between provider/nurse check-ins with patients, we can see that the F-value is 75.08 and the p-value is 6.79e-14 (6.79 x 10^-14). Our F-value indicates that there is a large between-group variance, compared to within-group variance. In addition, the p-value indicates that it is statistically signifcant at a 90%, 95%, or 99% Confidence Interval. 

See ANOVA.r for the code. 

We can also compare descriptive statistics (median, IQR) for the current system and C.O.R.G.I. In addition to the ANOVA test, we can see that the median wait time between visits is much lower with the C.O.R.G.I. system. 

<img width="1356" height="832" alt="image" src="https://github.com/user-attachments/assets/15f91d22-3695-424f-8baa-f3381d000228" />


