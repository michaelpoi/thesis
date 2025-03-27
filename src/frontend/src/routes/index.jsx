import { RouterProvider, createBrowserRouter } from "react-router-dom";
import { useAuth } from "../provider/AuthProvider";
import { ProtectedRoute } from "./ProtectedRoute";
import Login from "../pages/Login";
import Home from "../pages/home";
import Register from "../pages/Register";
import Logout from "../pages/Logout";
import Scenario from "../pages/Scenario";
import MapList from "../pages/MapList";
import mapCreator from "../pages/MapCreator";
import MapCreator from "../pages/MapCreator";
import Result from "../pages/Result";
import OfflineScenario from "../pages/OfflineScenario";

const Routes = () => {
  const { token } = useAuth();

  // Define public routes accessible to all users
  const routesForPublic = [
    {
      path: "/about-us",
      element: <div>About Us</div>,
    },
  ];

  const routesForAuthenticatedOnly = [
    {
      path: "/",
      element: <ProtectedRoute />, // Wrap the component in ProtectedRoute
      children: [
        {
          path: "/",
          element: <Home/>,
        },
        {
          path: "/scenario/:id",
          element: <Scenario></Scenario>
        },
        {
          path: "/result/:id",
          element: <Result></Result>
        },
        {
          path: "/offline/:id",
          element: <OfflineScenario></OfflineScenario>
        },
        {
          path: "/profile",
          element: <div>User Profile</div>,
        },
        {
          path: "/logout",
          element: <Logout/>,
        },
        {
          path: "/maps",
          element: <MapList/>
        },
        {
          path: "/creator",
          element: <MapCreator/>
        }
      ],
    },
  ];

  // Define routes accessible only to non-authenticated users
  const routesForNotAuthenticatedOnly = [
    {
      path: "/login",
      element: <Login/>,
    },
    {
      path: "/register",
      element: <Register/>
    }

  ];

  // Combine and conditionally include routes based on authentication status
  const router = createBrowserRouter([
    ...routesForPublic,
    ...(!token ? routesForNotAuthenticatedOnly : []),
    ...routesForAuthenticatedOnly,
  ]);

  // Provide the router configuration using RouterProvider
  return <RouterProvider router={router} />;
};

export default Routes;