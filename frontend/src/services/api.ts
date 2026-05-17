import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

export const getHealth = () => api.get("/health").then((r) => r.data);
export const getCityWise = () =>
  api.get("/dashboard/city-wise").then((r) => r.data);
export const getCategoryWise = () =>
  api.get("/dashboard/category-wise").then((r) => r.data);
export const getSourceWise = () =>
  api.get("/dashboard/source-wise").then((r) => r.data);

// Fixed: FastAPI uses `per_page`, not `limit`. City/category go straight to API.
export const getListings = (
  page = 1,
  perPage = 20,
  city = "",
  category = "",
) => {
  const params: any = { page, per_page: perPage };
  if (city) params.city = city;
  if (category) params.category = category;
  return api.get("/listings", { params }).then((r) => r.data);
};

export default api;
