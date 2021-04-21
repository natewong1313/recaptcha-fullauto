from recaptcha_solver import RecaptchaSolver
import signal


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    rcs = RecaptchaSolver("https://www.google.com/recaptcha/api2/demo")
    recaptcha_token = rcs.solve()