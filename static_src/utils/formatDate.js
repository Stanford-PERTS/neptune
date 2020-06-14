function formatDate(str) {
  return new Date(str).toISOString().split('T')[0];
}

export default formatDate;
