"""Descriptive joint errors with a question-conditioned independence comparator."""
import math,random,statistics
from collections import Counter
def entropy(values):
 counts=Counter(values);n=len(values)
 return -sum((v/n)*math.log2(v/n) for v in counts.values()) if n else None
def joint(rows):
 n=len(rows)
 if not n:return None
 a=sum(x[0] for x in rows)/n;b=sum(x[1] for x in rows)/n;observed=sum(x[0] and x[1] for x in rows)/n
 return dict(n=n,pA=a,pB=b,observedJoint=observed,independentMarginalProduct=a*b,excess=observed-a*b)
def conditioned(cases):
 values=[joint(rows)['excess'] for rows in cases.values() if rows]
 return statistics.mean(values) if values else None
def conditional_permutation(cases,iterations=4000,seed=2026100804):
 observed=conditioned(cases);rng=random.Random(seed);null=[]
 for _ in range(iterations):
  sample={}
  for k,rows in cases.items():
   b=[x[1] for x in rows];rng.shuffle(b);sample[k]=list(zip([x[0] for x in rows],b))
  null.append(conditioned(sample))
 return dict(observedExcess=observed,nullMean=statistics.mean(null),oneSidedExploratoryP=(1+sum(x>=observed-1e-12 for x in null))/(iterations+1),iterations=iterations,scope='within-question shuffle of four repeats; not causal dependence or independent-user inference')
def family_bootstrap(cases,families,iterations=4000,seed=2026100805):
 names=sorted(set(families.values()));rng=random.Random(seed);values=[]
 for _ in range(iterations):
  selected={}
  for i,f in enumerate(rng.choices(names,k=len(names))):
   for k,rows in cases.items():
    if families[k]==f:selected[(i,k)]=rows
  values.append(conditioned(selected))
 values.sort()
 return dict(low=values[int(.025*iterations)],high=values[min(iterations-1,int(.975*iterations))],unit='whole family, all cases and repetitions',iterations=iterations,exploratory=True)
