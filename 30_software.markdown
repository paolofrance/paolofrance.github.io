---
layout: page
title: Software
permalink: /software/
---
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-Z07C4092J3"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-Z07C4092J3');
</script>
<meta name="google-site-verification" content="9unXf0AJi0aPBon8QJz0gFG9YFuIUYQhVOjDDDbwA0Y" />

<script type="text/x-mathjax-config">
  MathJax.Hub.Config({tex2jax: {inlineMath: [['$','$'], ['\\(','\\)']]}});
</script>
<script type="text/javascript"
  src="http://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
</script>




## Game Theory

### Differential Game Theory
The solution to the Two-Players, Linear-Quadratic, Differential Game-Theoretic Cooperative and Non-Cooperative cases is implemented in the [differential_gt GitHub repository](https://github.com/paolofrance/differential_gt) 

This repository implements solutions to the Cooperative and Non-cooperative problems defined as follows:

#### Non-Cooperative GT-MPC

$$\begin{split}
    & \min_{u_1}J_{1} (z,u_1,u_2)\\
    & \min_{u_2}J_{2} (z,u_1,u_2)\\
    & s.t. \; \dot{z} = Az+B_1 \, u_1 + B_2\, u_2 \\
    & z(t_0) =z_0
  \end{split}$$

#### Cooperative GT 

$$\begin{split}
    & \min_{u}J_{c}  =  \int_{0}^{\infty}( z^T\,Q_{c}\,z + u^T\,R_{c}\,u )\,dt \\
    & s.t. \; \dot{z} = A_{c}\,z_{c}+B_{c}u_{c} \\
    & z_c(t_0) =z_0
  \end{split}$$

More info about the GT formulation for the physical Human-Robot Interaction problems can be found in [Human–Robot Role Arbitration via Differential Game Theory.](https://ieeexplore.ieee.org/abstract/document/10275780), and in [Modeling and analysis of pHRI with Differential Game Theory](https://arxiv.org/abs/2307.10739).
This is the continuous version fo the discrete problem presented in [distributed mpc](#distributed-gt-mpc).

### Distributed GT-MPC 

The solution to the Two-Players, Linear-Quadratic, distributed Model Predictive Control Game-Theoretic Cooperative and Non-Cooperative cases is implemented in the [distributed_mpc GitHub repository](https://github.com/paolofrance/distributed_mpc). This is the discrete version fo the differential problem presented in [differential GT](#differential-game-theory).


## Robot control

### Fanuc Ros2 interface
The implementation of the hardware interface for the fanuc robots for ros2.
Please refer to the [GitHub repository](https://github.com/paolofrance/ros2_fanuc_interface)

### Scaled Velocity Controller
A ros2 controller that allows dynamic velocity scaling during the execution of a trajectory. It implements a FollowJointTrajectoryAction server, it behaves as the joint_trajectory_controller (from which it inherits). 
Fully compatible with Moveit!
Check out its documentation on the [GitHub repo](https://github.com/paolofrance/scaled_fjt_controller) 


