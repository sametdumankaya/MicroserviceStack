# Mr. F MAGI

An algorithmic trading architecture leveraging MAGI and STMX technology. STMX provides real-time services such as:
* streaming interfaces to US and world stock, futures, and forex markets with ability to handle > 100K symbols with millisecond level sample rates
* streaming interfaces to financial metadata and news sources
* intelligent stock trading agents that take trading ideas and optimally execute them based on knowledge of technical analysis, overall market conditions (fear, key index behavior, etc...), and proprietary trading algorithms
* support for backtesting on 10 years worth of data
* robust distributed computing with automatic failover to guarantee trading performance during network, subsystem, and other downages
* support for multiple modes including fully automated trading and different levels of hybrid human/computer aka Centaur Trading. Centaur trading includes multiple levels of automation
  * lowest automation level is orders of magnitude more efficient than any known day trading interface
  * highest level of automation enables trader to enter high level trading ideas for optimal execution by the system

To use this repository in simulation mode, access to an STMX_MrF redis instance is required. This redis instance will include support for real-time and simulated market data with millisecond sample rate as well as support for bi-directional pub/sub message passing used for monitoring and control. In addition the following software must be installed:

* 

To use this repository for live trading, a TDAmeritrade account, a TDAmeritrade development account with application key (free), and the STMX local client is required. Using the STMX local client will enable the secure use of the STMX backend services in zero trust mode. This means that at no time will the STMX backend have access to your TDAmeritrade account info (including id), application key, or other trading information. The STMX local library residing on the end-user machine will interact directly with TDAmeritrade API's to execute trades. Cloud based secure virtual machines also operating in zero trust mode are available to provide robust operation with failover support. In addition, the system supports creation of stop losses for each trade to minimize worst case scenario losses.
