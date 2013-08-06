package com.flozano.sillysleepfilter;

import java.io.IOException;
import java.util.Random;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.FilterConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.HttpServletRequest;

public class SleepFilter implements Filter {

	private static final Logger LOGGER = Logger.getLogger(SleepFilter.class
			.getName());

	private final Random random = new Random();

	private Pattern requestPattern;

	private int minSleepTime = 0;

	private int maxSleepTime = 0;

	public void init(FilterConfig filterConfig) throws ServletException {
		requestPattern = Pattern.compile(filterConfig
				.getInitParameter("pattern"));
		minSleepTime = Integer.parseInt(filterConfig
				.getInitParameter("min-sleep"));
		maxSleepTime = Integer.parseInt(filterConfig
				.getInitParameter("max-sleep"));
		LOGGER.warning("DON'T USE THIS SERVLET-FILTER IN PRODUCTION");
		LOGGER.info("Initialized: pattern = " + requestPattern
				+ ", minSleepTime=" + minSleepTime + ", maxSleepTime="
				+ maxSleepTime);
	}

	public void doFilter(ServletRequest request, ServletResponse response,
			FilterChain chain) throws IOException, ServletException {
		HttpServletRequest httpRequest = (HttpServletRequest) request;
		if (isMatch(httpRequest)) {
			sleep();
		}
	}

	private void sleep() {
		try {
			int msecs = random.nextInt(maxSleepTime - minSleepTime)
					+ minSleepTime;
			LOGGER.info("Waiting " + msecs + " msecs");
			Thread.sleep(msecs);
		} catch (InterruptedException e) {
			e.printStackTrace();
		}
	}

	private boolean isMatch(HttpServletRequest request) {
		Matcher m = requestPattern.matcher(request.getRequestURI());
		if (m.matches()) {
			LOGGER.info("Request matches: " + request.getRequestURI());
			return true;
		}
		return false;
	}

	public void destroy() {

	}

}
