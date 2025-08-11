/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast, { Toaster } from "react-hot-toast";

const AuthPage: React.FC = () => {
  // States for register/login
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(true);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Handler for Register/Login
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const endpoint = isRegister
      ? "http://localhost:5000/api/auth/register"
      : "http://localhost:5000/api/auth/login";

    // Build payload
    let payload: any = {};
    if (isRegister) {
      payload = { username, email, password };
    } else {
      // For login, allow either username OR email
      payload = username
        ? { username, password }
        : { email, password };
      if (!username && !email) {
        toast.error("Enter username or email");
        setLoading(false);
        return;
      }
    }

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        toast.error(data.error || "Something went wrong");
        setLoading(false);
        return;
      }

      // Save token, username, email to localStorage
      localStorage.setItem("token", data.token);
      localStorage.setItem("username", data.username || username);
      if (data.email) localStorage.setItem("email", data.email);

      toast.success(isRegister ? "Registration successful!" : "Login successful!");

      setTimeout(() => {
        navigate("/chat");
      }, 900);
    } catch (err) {
      toast.error("Network error");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-white flex flex-col md:flex-row items-center justify-center">
      <Toaster position="top-center" />
      {/* Left Panel */}
      <div
        className="hidden md:flex flex-col justify-between w-1/2 px-14 pt-28 text-black relative overflow-hidden"
        style={{ minHeight: "100vh" }}
      >
        <div
          className="absolute inset-0 z-0"
          style={{
            background:
              "linear-gradient(120deg, #2467e7 0%, #9345f2 40%, #ff96b3 75%, #ffb78c 100%)",
          }}
        />
        <img
          src="/london-skyline.png"
          alt="London skyline"
          className="absolute bottom-0 left-0 w-full opacity-30 z-10"
          style={{ pointerEvents: "none" }}
        />
        <div className="relative z-20">
          <h1 className="text-5xl font-extrabold leading-tight mb-5">
            <span className="block text-white">Learn, Discover &amp;</span>
            <span className="block text-white/90">Automate in One Place.</span>
          </h1>
          <p className="mt-8 text-xl font-light text-white/80">
            <b>BritMentor</b> — Your smart UK study assistant.
          </p>
          <div className="mt-10 bg-white/20 p-5 rounded-2xl backdrop-blur-md">
            <div className="mb-2">
              <span className="font-bold text-white">
                Q: How do I apply to universities in London?
              </span>
            </div>
            <div className="pl-8 mb-1">
              <span className="inline-block px-3 py-1 bg-blue-700 text-white rounded-full font-semibold text-sm">
                BritMentor
              </span>
            </div>
            <div className="pl-8 flex items-baseline">
              <span className="font-bold text-green-300 mr-2">A:</span>
              <span className="text-white/90">
                I can guide you through the process! Start by preparing your academic documents, English test scores, and personal statement.
                Would you like a step-by-step checklist?
              </span>
            </div>
          </div>
        </div>
        <div className="mt-8 text-xs text-white/80 relative z-20">
          🇬🇧 Powered by BritMentor &mdash; Inspired by UK Excellence
        </div>
      </div>
      {/* Right Panel */}
      <div className="w-full md:w-1/2 flex flex-col items-center">
        <div className="w-full max-w-md pt-16">
          <h2 className="text-3xl md:text-4xl font-semibold text-center mb-2 mt-2 text-black">
            {isRegister ? "Sign up with No Hassle" : "Sign in to your account"}
          </h2>
          <p className="text-center text-gray-500 mb-8">
            Get Your Free UK Counseling {isRegister ? "sign up" : "sign in"} for a
            free account today
          </p>
          <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
            {isRegister ? (
              <>
                <div>
                  <label
                    className="block text-gray-700 font-medium mb-1"
                    htmlFor="username"
                  >
                    Username*
                  </label>
                  <input
                    type="text"
                    id="username"
                    required
                    placeholder="Enter a unique username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-600 transition text-gray-900 font-normal"
                  />
                </div>
                <div>
                  <label
                    className="block text-gray-700 font-medium mb-1"
                    htmlFor="email"
                  >
                    Email Address*
                  </label>
                  <input
                    type="email"
                    id="email"
                    required
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-600 transition text-gray-900 font-normal"
                  />
                </div>
              </>
            ) : (
              <>
                <div>
                  <label
                    className="block text-gray-700 font-medium mb-1"
                    htmlFor="userOrEmail"
                  >
                    Username or Email*
                  </label>
                  <input
                    type="text"
                    id="userOrEmail"
                    required
                    placeholder="Enter your username or email"
                    value={username || email}
                    onChange={(e) => {
                      // Allow entering either
                      if (e.target.value.includes("@")) {
                        setEmail(e.target.value);
                        setUsername("");
                      } else {
                        setUsername(e.target.value);
                        setEmail("");
                      }
                    }}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-600 transition text-gray-900 font-normal"
                  />
                </div>
              </>
            )}
            <div>
              <label
                className="block text-gray-700 font-medium mb-1"
                htmlFor="password"
              >
                Password*
              </label>
              <input
                type="password"
                id="password"
                required
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-600 transition text-gray-900 font-normal"
              />
            </div>
            <button
              type="submit"
              className={`w-full py-3 rounded-xl mt-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-lg transition ${loading ? "opacity-50 cursor-not-allowed" : ""
                }`}
              disabled={loading}
            >
              {loading
                ? isRegister
                  ? "Registering..."
                  : "Signing in..."
                : isRegister
                  ? "Get started free"
                  : "Sign in"}
            </button>
          </form>
          <div className="flex justify-center items-center gap-2 mt-7 mb-5">
            <span className="h-px flex-1 bg-gray-200"></span>
            <span className="text-gray-400 text-sm">Or better yet…</span>
            <span className="h-px flex-1 bg-gray-200"></span>
          </div>
          <button
            className="w-full mb-4 py-3 flex items-center justify-center border border-gray-200 rounded-xl bg-white text-gray-700 hover:bg-gray-50 font-semibold text-base transition"
            type="button"
            onClick={() => toast("Google login coming soon!")}
          >
            <img
              src="https://www.svgrepo.com/show/475656/google-color.svg"
              alt="Google"
              className="w-5 h-5 mr-2"
            />
            Continue with Google
          </button>
          <div className="text-center text-sm text-gray-700 mb-2">
            {isRegister ? (
              <>
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => setIsRegister(false)}
                  className="text-blue-700 font-bold hover:underline"
                >
                  Login
                </button>
              </>
            ) : (
              <>
                Don't have an account?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setIsRegister(true);
                    setUsername("");
                    setEmail("");
                  }}
                  className="text-blue-700 font-bold hover:underline"
                >
                  Register
                </button>
              </>
            )}
          </div>
        </div>
        <div className="mt-8 mb-2 text-xs text-gray-400 text-center max-w-xs mx-auto">
          By registering for an account, you are consenting to our{" "}
          <a href="#" className="underline">
            Terms of Service
          </a>{" "}
          and confirming that you have reviewed and accepted the{" "}
          <a href="#" className="underline">
            Global Privacy Statement
          </a>
          .
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
