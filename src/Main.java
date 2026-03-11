public class Main {
    public static void main(String[] args) {
        Personnage guerrierNain = new Personnage("Thorin", new Nain(), new Guerrier());
        guerrierNain.afficher();

        System.out.println();

        Personnage magicienElfe = new Personnage("Legolas", new Elfe(), new Magicien());
        magicienElfe.afficher();

        System.out.println();

        Personnage pretreHumain = new Personnage("Aldric", new Humain(), new Pretre());
        pretreHumain.afficher();

        System.out.println();

        Personnage voleurDemiOrque = new Personnage("Grok", new DemiOrque(), new Voleur());
        voleurDemiOrque.afficher();

        System.out.println();

        Personnage rodeurDemiElfe = new Personnage("Elara", new DemiElfe(), new Rodeur());
        rodeurDemiElfe.afficher();
    }
}
