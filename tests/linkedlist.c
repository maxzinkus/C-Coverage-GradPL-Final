#include <stdlib.h>
#include <stdio.h>

struct list_el {
   int val;
   struct list_el * next;
};

typedef struct list_el item;

int main() {
   item * curr, * head;
   int i;

   head = NULL;

   for(i=1;i<=10;i++) {
      curr = (item *)malloc(sizeof(item));
      curr->val = i;
      curr->next  = head;
      head = curr;
   }

   curr = head;

   while(curr) {
      printf("%d\n", curr->val);
      head = curr;
      curr = curr->next ;
      free(head);
   }
}

