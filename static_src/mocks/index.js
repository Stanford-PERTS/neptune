import capitalize from 'capitalize';
import faker from 'faker';

export const createUid = (type = '') => {
  const uid = faker.random
    .uuid()
    .replace(/-/g, '')
    .substr(1, 12);

  return `${capitalize(type)}_${uid}`;
};
